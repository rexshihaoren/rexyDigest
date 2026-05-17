"""YoutubeAdapter — channel video metadata via YouTube's public Atom feed,
plus best-effort transcript via `youtube-transcript-api`.

Config (per `config/sources/youtube.toml`):

  source_type = "youtube"

  [[channels]]
  channel_id     = "UCoookXUzPciGrEZEXmh4Jjg"   # OR `user` / `feed_url`
  default_author = "Andrej Karpathy"
  kol            = "karpathy"                   # optional: KOL key for boost / bypass

ADR-0003 invariants honoured:
- Adapter is pure; framework owns persistence.
- Transcripts are best-effort. Missing transcript -> ``payload_kind=metadata_only``
  with description as a fallback summary; never a hard fetch failure.
- Per-Item failures (e.g. one transcript fetch raising) are caught and that
  Item is yielded as ``metadata_only``; only completely unusable channel
  feeds raise ``AdapterError``.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Callable, Iterator

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
from .rss_adapter import parse_feed_document  # reuses test-injectable hook


# Test seam: production fetches via youtube-transcript-api. Tests override this.
TranscriptFetcher = Callable[[str], str | None]


def _default_fetch_transcript(video_id: str) -> str | None:
    """Lazy import — `youtube-transcript-api` is optional; if missing, skip."""

    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover - exercised only without dep
        return None

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        # Concatenate snippet text — order is the order the API returns.
        chunks: list[str] = []
        for s in transcript:
            text = getattr(s, "text", None)
            if text is None and isinstance(s, dict):
                text = s.get("text")
            if text:
                chunks.append(str(text).strip())
        joined = "\n".join(c for c in chunks if c)
        return joined or None
    except Exception:  # pragma: no cover - per-video network/auth failures
        return None


fetch_transcript: TranscriptFetcher = _default_fetch_transcript


class YoutubeAdapter:
    name: str
    source_type: SourceType = SourceType.YOUTUBE

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        channels = config.get("channels") or []
        if not channels:
            raise AdapterError(
                f"{name}: youtube adapter requires a non-empty `channels` list"
            )
        self.channels: list[dict[str, Any]] = []
        for entry in channels:
            url = _channel_feed_url(entry)
            self.channels.append({
                "url": url,
                "default_author": (entry.get("default_author") or "").strip(),
                "kol": (entry.get("kol") or "").strip(),
            })

    def fetch(self, window: Window) -> Iterator[FetchedItem]:
        for channel_cfg in self.channels:
            yield from self._fetch_one(channel_cfg, window)

    def _fetch_one(
        self, channel_cfg: dict[str, Any], window: Window,
    ) -> Iterator[FetchedItem]:
        parsed = parse_feed_document(channel_cfg["url"])
        if getattr(parsed, "bozo", False) and not parsed.entries:
            raise AdapterError(
                f"{self.name}: failed to parse channel feed "
                f"{channel_cfg['url']!r}: {getattr(parsed, 'bozo_exception', None)!r}"
            )

        feed_author = _feed_author(parsed) or channel_cfg["default_author"]
        kol_tag = channel_cfg["kol"]

        for entry in parsed.entries:
            published_at = _entry_date(entry)
            if published_at is None or not window.contains(published_at):
                continue

            video_id = _video_id(entry)
            if not video_id:
                continue

            canonical_url = f"https://www.youtube.com/watch?v={video_id}"
            description = _entry_description(entry)

            transcript: str | None = None
            try:
                transcript = fetch_transcript(video_id)
            except Exception:  # defensive — never fail the whole fetch
                transcript = None

            payload_text: str | None
            if transcript:
                payload_text = transcript
                payload_kind = PayloadKind.FULL_TEXT
            elif description:
                payload_text = description
                payload_kind = PayloadKind.EXTRACT
            else:
                payload_text = None
                payload_kind = PayloadKind.METADATA_ONLY

            author = (
                _author_from_entry(entry)
                or feed_author
                or "(unknown)"
            )

            topics_raw = [t.term for t in (entry.get("tags") or []) if getattr(t, "term", None)]
            if kol_tag:
                marker = f"kol:{kol_tag.lower()}"
                if marker not in topics_raw:
                    topics_raw.insert(0, marker)

            item = Item(
                id=make_item_id(SourceType.YOUTUBE, video_id, canonical_url),
                source_type=SourceType.YOUTUBE,
                source_native_id=video_id,
                canonical_url=canonical_url,
                title=(entry.get("title") or "(untitled)").strip(),
                author=author,
                published_at=published_at,
                type="video",
                topics_raw=topics_raw,
                payload_kind=payload_kind,
                payload_ref=None,
                fetched_at=now_utc(),
                adapter=self.name,
            )
            yield FetchedItem(
                item=item,
                payload=payload_text if payload_text is not None else None,
                payload_suffix=".txt",
            )


_CHANNEL_ID_RE = re.compile(r"^UC[0-9A-Za-z_-]{20,30}$")
_VIDEO_ID_FROM_URL = re.compile(r"(?:v=|/watch\?v=|youtu\.be/|/shorts/)([0-9A-Za-z_-]{11})")
_YT_VIDEO_PREFIX = "yt:video:"


def _channel_feed_url(entry: dict[str, Any]) -> str:
    if not isinstance(entry, dict):
        raise AdapterError("youtube: each channels entry must be a table")
    feed_url = (entry.get("feed_url") or "").strip()
    if feed_url:
        return feed_url
    channel_id = (entry.get("channel_id") or "").strip()
    if channel_id:
        if not _CHANNEL_ID_RE.match(channel_id):
            raise AdapterError(
                f"youtube: channel_id {channel_id!r} does not look like a "
                f"YouTube channel id (expected UC… 22–32 chars)"
            )
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    user = (entry.get("user") or "").strip()
    if user:
        return f"https://www.youtube.com/feeds/videos.xml?user={user}"
    raise AdapterError(
        "youtube: each channels entry needs `channel_id`, `user`, or `feed_url`"
    )


def _entry_date(entry: Any) -> date | None:
    parsed = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
    )
    if parsed is None:
        return None
    try:
        return datetime(*parsed[:6], tzinfo=timezone.utc).date()
    except (TypeError, ValueError):
        return None


def _video_id(entry: Any) -> str | None:
    """Resolve the canonical YouTube videoId.

    feedparser surfaces ``<yt:videoId>`` as ``entry.yt_videoid``; we also fall
    back to extracting from the entry id (``yt:video:VIDEOID``) or link URL.
    """

    direct = (
        entry.get("yt_videoid")
        or entry.get("yt:videoid")
        or entry.get("videoid")
    )
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    eid = entry.get("id") or entry.get("guid") or ""
    if isinstance(eid, str) and eid.startswith(_YT_VIDEO_PREFIX):
        return eid[len(_YT_VIDEO_PREFIX):].strip() or None

    link = (entry.get("link") or "").strip()
    if link:
        m = _VIDEO_ID_FROM_URL.search(link)
        if m:
            return m.group(1)
    return None


def _entry_description(entry: Any) -> str:
    summary = entry.get("summary") or ""
    if isinstance(summary, str):
        text = summary.strip()
        if text:
            return text
    content = entry.get("content") or []
    for c in content:
        value = getattr(c, "value", None) or (c.get("value") if isinstance(c, dict) else None)
        if value:
            return str(value).strip()
    return ""


def _author_from_entry(entry: Any) -> str:
    raw = entry.get("author")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    authors = entry.get("authors")
    if not authors:
        return ""
    names: list[str] = []
    for a in authors:
        name = getattr(a, "name", None) or (a.get("name") if isinstance(a, dict) else None)
        if name:
            names.append(name)
    return ", ".join(names)


def _feed_author(parsed: Any) -> str:
    feed = getattr(parsed, "feed", None) or {}
    if isinstance(feed, dict):
        title = (feed.get("title") or "").strip()
        if title:
            return title
        author = (feed.get("author") or "").strip()
        if author:
            return author
    return ""
