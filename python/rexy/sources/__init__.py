"""Source Adapter port and shared adapter helpers.

ADR-0003 defines the contract: every adapter satisfies the SourceAdapter
Protocol. Adapters are pure (no filesystem) — the framework owns persistence.
"""

from __future__ import annotations

from typing import Any, Iterator, Protocol, runtime_checkable

from ..domain import FetchedItem, SourceType, Window


@runtime_checkable
class SourceAdapter(Protocol):
    """One adapter per Source family. Yields fully-normalised Items.

    Contract:
      - `fetch(window)` MUST yield only Items whose `published_at` falls
        inside `window` (per ADR-0006 — Window owned by ingestion).
      - Adapter is responsible for URL canonicalisation, ID extraction,
        and choosing `payload_kind` honestly.
      - Adapter MUST set `Item.adapter` to its own `name` for provenance.
      - Adapter MAY raise on hard failures (network, auth) — the framework
        records the error in the run file and continues with other adapters.
    """

    name: str
    source_type: SourceType

    def fetch(self, window: Window) -> Iterator[FetchedItem]: ...


class AdapterError(Exception):
    """Raised by adapters for non-recoverable per-adapter failures.

    Per-Item failures should NOT raise — they should yield a metadata-only
    or unavailable Item if a stable id can be derived, or be silently
    skipped if not. This exception is for "I cannot fetch from this source
    at all right now" cases (network outage, API auth, config missing).
    """


def build_adapter(name: str, source_type: str, config: dict[str, Any]) -> SourceAdapter:
    """Instantiate an adapter by source_type. Used by the registry.

    Imports happen lazily so a missing optional dep (e.g. arxiv package)
    only breaks the adapter that needs it, not the whole CLI.
    """

    st = SourceType(source_type)
    if st is SourceType.ARXIV:
        from .arxiv_adapter import ArxivAdapter
        return ArxivAdapter(name=name, config=config)
    if st is SourceType.RSS:
        from .rss_adapter import RssAdapter
        return RssAdapter(name=name, config=config)
    if st is SourceType.YOUTUBE:
        from .youtube_adapter import YoutubeAdapter
        return YoutubeAdapter(name=name, config=config)
    raise AdapterError(
        f"No adapter implementation registered for source_type={source_type!r}; "
        f"only {[t.value for t in SourceType]} are valid enum values"
    )
