"""Stage 1 — Pre-filter (deterministic Python).

Coarse gates that should drop obviously-irrelevant Items before any LLM
spend. Anything an embedding/LLM judgement would catch but cheaper signals
won't is intentionally NOT done here — that belongs to the per-Item LLM
stage (`summarise.py`).
"""

from __future__ import annotations

from collections.abc import Iterable

from ..corpus.payloads_store import PayloadsStore
from ..domain import Item, PayloadKind, Window
from .config import GeneratorConfig


def prefilter(
    items: Iterable[Item],
    window: Window,
    config: GeneratorConfig,
    payloads: PayloadsStore,
    min_keyword_hits: int = 1,
) -> list[Item]:
    """Return Items that survive the coarse gates.

    Drops:
      - Out-of-Window (defensive: ingestion already filters, but a corpus
        query may legitimately span more)
      - `payload_kind=UNAVAILABLE` and title also lacks any keyword hit
      - `payload_kind=METADATA_ONLY` AND title has zero keyword hits
        (we have no body to fall back to)
      - Items with fewer than `min_keyword_hits` keyword hits across
        title + topics_raw + payload (if any)
    """

    keywords = [kw.lower() for kw in config.all_keywords]
    kept: list[Item] = []

    for item in items:
        if not window.contains(item.published_at):
            continue

        haystack_parts = [item.title.lower(), " ".join(item.topics_raw).lower()]
        if item.payload_kind in (PayloadKind.EXTRACT, PayloadKind.FULL_TEXT) and item.payload_ref:
            try:
                haystack_parts.append(payloads.read(item.payload_ref).lower())
            except FileNotFoundError:
                # corpus inconsistency; treat as if no payload
                pass
        haystack = "\n".join(haystack_parts)

        hits = sum(1 for kw in keywords if kw in haystack)
        if hits < min_keyword_hits:
            continue

        kept.append(item)

    return kept
