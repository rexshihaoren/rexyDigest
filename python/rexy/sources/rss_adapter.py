"""RssAdapter — fetches entries from RSS / Atom feeds via `feedparser`.

Covers blogs, podcast feeds, and any other RSS/Atom source. Per ADR-0003,
the YouTube and dedicated podcast adapters are deferred — RSS handles the
majority of long-tail blog and podcast feeds in the meantime.

Config (per `config/sources/rss.toml`):

  [[rss.feeds]]
  url            = "https://lilianweng.github.io/index.xml"
  type           = "blog"          # blog | podcast — written to Item.type
  default_author = "Lilian Weng"   # used when feed entries lack <author>

  [[rss.feeds]]
  url            = "https://www.latent.space/feed"
  type           = "blog"
  default_author = "Latent Space"
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable, Iterator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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


_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")
_VALID_ITEM_TYPES = {"blog", "podcast", "video", "talk", "paper"}


def _default_parse_feed_document(url: str) -> Any:
    """Parse a feed URL or local path with feedparser (production default)."""

    try:
        import feedparser
    except ImportError as exc:  # pragma: no cover
        raise AdapterError(
            "rss: the `feedparser` package is not installed; "
            "run `pip install -r requirements.txt`"
        ) from exc
    return feedparser.parse(url)


# Tests may assign a stub; production uses feedparser via _default_parse_feed_document.
parse_feed_document: Callable[[str], Any] = _default_parse_feed_document


class RssAdapter:
    name: str
    source_type: SourceType = SourceType.RSS

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        feeds = config.get("feeds") or []
        if not feeds:
            raise AdapterError(
                f"{name}: rss adapter requires a non-empty `feeds` list"
            )
        self.feeds: list[dict[str, Any]] = []
        for entry in feeds:
            if not entry.get("url"):
                raise AdapterError(f"{name}: every feed entry needs a `url`")
            item_type = entry.get("type", "blog")
            if item_type not in _VALID_ITEM_TYPES:
                raise AdapterError(
                    f"{name}: feed type {item_type!r} not in {_VALID_ITEM_TYPES}"
                )
            self.feeds.append({
                "url": entry["url"],
                "type": item_type,
                "default_author": entry.get("default_author", ""),
            })

    def fetch(self, window: Window) -> Iterator[FetchedItem]:
        for feed_cfg in self.feeds:
            yield from self._fetch_one(feed_cfg, window)

    def _fetch_one(
        self, feed_cfg: dict[str, Any], window: Window,
    ) -> Iterator[FetchedItem]:
        parsed = parse_feed_document(feed_cfg["url"])
        # feedparser does not raise on HTTP errors; surface them as adapter errors
        # only when nothing usable was returned.
        if parsed.bozo and not parsed.entries:
            raise AdapterError(
                f"{self.name}: failed to parse feed {feed_cfg['url']!r}: "
                f"{parsed.bozo_exception!r}"
            )

        for entry in parsed.entries:
            published_at = _entry_date(entry)
            if published_at is None or not window.contains(published_at):
                continue

            link = (entry.get("link") or "").strip()
            canonical_url = _canonicalise_url(link) if link else ""
            if not canonical_url:
                continue  # cannot identify or render without a URL

            # Some feeds (e.g. Simon Willison's atom) put the entry URL in
            # `id`, which produces 100+ char Item IDs and unwieldy payload
            # filenames. Treat URL-shaped GUIDs as "no native id" so the
            # url-sha1 fallback kicks in and the canonical URL stays the
            # human-readable identity.
            raw_native_id = entry.get("id") or entry.get("guid") or None
            native_id = raw_native_id if _is_compact_guid(raw_native_id) else None
            item_id = make_item_id(SourceType.RSS, native_id, canonical_url)

            extract = _extract_text(entry)
            payload_kind = (
                PayloadKind.EXTRACT if extract else PayloadKind.METADATA_ONLY
            )

            author = (
                entry.get("author")
                or _author_from_authors(entry.get("authors"))
                or feed_cfg["default_author"]
                or _host_of(canonical_url)
            )

            topics_raw = [
                t.term for t in (entry.get("tags") or [])
                if getattr(t, "term", None)
            ]

            item = Item(
                id=item_id,
                source_type=SourceType.RSS,
                source_native_id=native_id,
                canonical_url=canonical_url,
                title=(entry.get("title") or "(untitled)").strip(),
                author=author,
                published_at=published_at,
                type=feed_cfg["type"],
                topics_raw=topics_raw,
                payload_kind=payload_kind,
                payload_ref=None,
                fetched_at=now_utc(),
                adapter=self.name,
            )
            yield FetchedItem(
                item=item,
                payload=extract if payload_kind is PayloadKind.EXTRACT else None,
                payload_suffix=".txt",
            )


def _entry_date(entry: Any) -> date | None:
    parsed = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
        or entry.get("created_parsed")
    )
    if parsed is None:
        return None
    try:
        return datetime(*parsed[:6], tzinfo=timezone.utc).date()
    except (TypeError, ValueError):
        return None


def _extract_text(entry: Any) -> str:
    """Best-effort plain-text extract from an entry's summary/content."""
    candidates: list[str] = []
    summary = entry.get("summary")
    if summary:
        candidates.append(summary)
    content = entry.get("content")
    if content:
        for c in content:
            value = getattr(c, "value", None) or (c.get("value") if isinstance(c, dict) else None)
            if value:
                candidates.append(value)
    if not candidates:
        return ""
    return _strip_html(max(candidates, key=len)).strip()


def _strip_html(html: str) -> str:
    """Minimal HTML stripper — good enough for feed summaries."""
    import re

    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _author_from_authors(authors: Any) -> str:
    if not authors:
        return ""
    names: list[str] = []
    for a in authors:
        name = getattr(a, "name", None) or (a.get("name") if isinstance(a, dict) else None)
        if name:
            names.append(name)
    return ", ".join(names)


def _canonicalise_url(url: str) -> str:
    """Strip tracking params and fragment; lowercase host."""
    try:
        parts = urlparse(url)
    except ValueError:
        return ""
    if not parts.scheme or not parts.netloc:
        return ""
    cleaned_q = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not any(k.lower().startswith(p) for p in _TRACKING_PREFIXES)
    ]
    return urlunparse((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path,
        parts.params,
        urlencode(cleaned_q),
        "",  # drop fragment
    ))


def _host_of(url: str) -> str:
    try:
        return urlparse(url).netloc or "(unknown)"
    except ValueError:
        return "(unknown)"


def _is_compact_guid(guid: str | None) -> bool:
    """True for stable, short, non-URL GUIDs (e.g. ``tag:`` URIs, UUIDs).

    URL-shaped GUIDs make terrible Item IDs because they're long and contain
    many filesystem-unfriendly characters. We prefer the url-sha1 fallback
    in those cases.
    """
    if not guid:
        return False
    if guid.startswith(("http://", "https://")):
        return False
    return len(guid) <= 80
