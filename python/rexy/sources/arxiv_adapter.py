"""ArxivAdapter — fetches papers from arXiv via the `arxiv` package.

Config (per `config/sources/arxiv.toml`):

  [arxiv]
  categories   = ["cs.AI", "cs.LG"]                # required, non-empty
  keywords     = ["agent", "simulation", "LLM"]    # optional title/abstract filter
  max_results  = 200                               # cap per fetch (default 200)

Notes
-----
- arXiv `entry_id` looks like ``http://arxiv.org/abs/2401.12345v2``. We strip
  the version suffix for stable identity (`Item.id = "arxiv:2401.12345"`).
- Each Item carries the abstract as ``payload_kind=EXTRACT``. Full PDF text
  is deferred (would require pdf-to-text and bigger payloads).
- Results are sorted by submission date descending; we stop iterating once
  we cross below the window's start date.
"""

from __future__ import annotations

import re
from datetime import date, timezone
from typing import Any, Iterator

from ..domain import (
    FetchedItem,
    Item,
    PayloadKind,
    SourceType,
    Window,
    make_item_id,
    now_utc,
)
from . import AdapterError


_ARXIV_VERSION_RE = re.compile(r"v\d+$")


class ArxivAdapter:
    name: str
    source_type: SourceType = SourceType.ARXIV

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.categories: list[str] = list(config.get("categories") or [])
        if not self.categories:
            raise AdapterError(
                f"{name}: arxiv adapter requires a non-empty `categories` config list"
            )
        self.keywords: list[str] = [k.lower() for k in (config.get("keywords") or [])]
        self.max_results: int = int(config.get("max_results", 200))

    def fetch(self, window: Window) -> Iterator[FetchedItem]:
        try:
            import arxiv
        except ImportError as exc:  # pragma: no cover - exercised in env without arxiv
            raise AdapterError(
                f"{self.name}: the `arxiv` package is not installed; "
                "run `pip install -r requirements.txt`"
            ) from exc

        query = " OR ".join(f"cat:{cat}" for cat in self.categories)
        search = arxiv.Search(
            query=query,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        # arXiv's API throttles aggressively; conservative defaults so a
        # repeated dev run doesn't hit 429. Tunable later via config.
        client = arxiv.Client(page_size=100, delay_seconds=5.0, num_retries=5)

        for result in client.results(search):
            published_at = _to_date(result.published)
            if published_at > window.end:
                # newer than window — keep scanning, results are descending
                continue
            if published_at < window.start:
                # crossed below the window; results stay older from here
                break

            if not self._matches_keywords(result.title, result.summary):
                continue

            native_id = _strip_version(_arxiv_id_from_entry(result.entry_id))
            canonical_url = f"https://arxiv.org/abs/{native_id}"
            abstract = (result.summary or "").strip()

            item = Item(
                id=make_item_id(SourceType.ARXIV, native_id, canonical_url),
                source_type=SourceType.ARXIV,
                source_native_id=native_id,
                canonical_url=canonical_url,
                title=(result.title or "").strip().replace("\n", " "),
                author=", ".join(a.name for a in (result.authors or [])) or "(unknown)",
                published_at=published_at,
                type="paper",
                topics_raw=list(result.categories or []),
                payload_kind=PayloadKind.EXTRACT if abstract else PayloadKind.METADATA_ONLY,
                payload_ref=None,  # framework fills this in
                fetched_at=now_utc(),
                adapter=self.name,
            )
            yield FetchedItem(
                item=item,
                payload=abstract if abstract else None,
                payload_suffix=".txt",
            )

    def _matches_keywords(self, title: str | None, summary: str | None) -> bool:
        if not self.keywords:
            return True
        haystack = ((title or "") + "\n" + (summary or "")).lower()
        return any(k in haystack for k in self.keywords)


def _arxiv_id_from_entry(entry_id: str) -> str:
    """Extract bare arXiv id from an entry_id URL like
    ``http://arxiv.org/abs/2401.12345v2`` -> ``2401.12345v2``.
    """
    return entry_id.rstrip("/").split("/")[-1]


def _strip_version(native_id: str) -> str:
    return _ARXIV_VERSION_RE.sub("", native_id)


def _to_date(dt: Any) -> date:
    """arxiv.Result.published is a tz-aware datetime; we want UTC date."""
    if dt is None:
        raise AdapterError("arxiv result missing published date")
    if hasattr(dt, "astimezone"):
        return dt.astimezone(timezone.utc).date()
    return dt  # already a date
