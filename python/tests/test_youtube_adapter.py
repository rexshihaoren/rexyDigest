"""YoutubeAdapter unit tests using a synthetic Atom-flavoured feed.

Mirrors `test_rss_adapter`: we patch the module-level `parse_feed_document`
hook with a stdlib stub so these tests pass without the optional
`feedparser` dependency, and inject a deterministic transcript fetcher so
the network is never hit.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from rexy.domain import PayloadKind, SourceType, Window
from rexy.sources import youtube_adapter as yt_mod
from rexy.sources.youtube_adapter import YoutubeAdapter


WINDOW = Window.parse("2026-05-03/2026-05-10")


def _entry(
    *,
    title: str,
    video_id: str,
    pub_iso: str = "2026-05-05T12:00:00Z",
    summary: str | None = None,
    author: str | None = None,
    link: str | None = None,
) -> dict[str, Any]:
    # Match feedparser's surface used by the adapter
    parts = pub_iso.replace("Z", "+00:00").split("T")
    y, m, d = (int(x) for x in parts[0].split("-"))
    h, mi, _s = parts[1].split("+")[0].split(":")
    out: dict[str, Any] = {
        "title": title,
        "link": link or f"https://www.youtube.com/watch?v={video_id}",
        "id": f"yt:video:{video_id}",
        "yt_videoid": video_id,
        "published_parsed": (y, m, d, int(h), int(mi), 0, 0, 0, 0),
    }
    if summary:
        out["summary"] = summary
    if author:
        out["authors"] = [SimpleNamespace(name=author)]
    return out


def _stub_feed(entries: list[dict[str, Any]], feed_title: str = "Channel") -> Any:
    return SimpleNamespace(
        entries=entries,
        feed={"title": feed_title},
        bozo=False,
        bozo_exception=None,
    )


def _adapter(channels: list[dict[str, Any]] | None = None) -> YoutubeAdapter:
    return YoutubeAdapter(
        name="youtube",
        config={
            "channels": channels
            or [
                {
                    "channel_id": "UCoookXUzPciGrEZEXmh4Jjg",
                    "default_author": "Andrej Karpathy",
                    "kol": "karpathy",
                }
            ]
        },
    )


def test_yields_full_text_when_transcript_available():
    adapter = _adapter()
    entries = [_entry(title="A talk on agents", video_id="abc12345678")]
    transcripts = {"abc12345678": "full transcript text"}

    with patch.object(yt_mod, "parse_feed_document", lambda url: _stub_feed(entries)), \
            patch.object(yt_mod, "fetch_transcript", lambda vid: transcripts.get(vid)):
        items = list(adapter.fetch(WINDOW))

    assert len(items) == 1
    fi = items[0]
    assert fi.item.source_type is SourceType.YOUTUBE
    assert fi.item.id == "youtube:abc12345678"
    assert fi.item.canonical_url == "https://www.youtube.com/watch?v=abc12345678"
    assert fi.item.type == "video"
    assert fi.item.payload_kind is PayloadKind.FULL_TEXT
    assert fi.payload == "full transcript text"
    assert "kol:karpathy" in fi.item.topics_raw


def test_falls_back_to_description_when_transcript_missing():
    adapter = _adapter()
    entries = [_entry(
        title="A talk", video_id="vid99999999",
        summary="An interesting video description",
    )]

    with patch.object(yt_mod, "parse_feed_document", lambda url: _stub_feed(entries)), \
            patch.object(yt_mod, "fetch_transcript", lambda vid: None):
        items = list(adapter.fetch(WINDOW))

    assert len(items) == 1
    fi = items[0]
    assert fi.item.payload_kind is PayloadKind.EXTRACT
    assert fi.payload == "An interesting video description"


def test_metadata_only_when_no_transcript_no_description():
    adapter = _adapter()
    entries = [_entry(title="Bare entry", video_id="bare1234567")]

    with patch.object(yt_mod, "parse_feed_document", lambda url: _stub_feed(entries)), \
            patch.object(yt_mod, "fetch_transcript", lambda vid: None):
        items = list(adapter.fetch(WINDOW))

    fi = items[0]
    assert fi.item.payload_kind is PayloadKind.METADATA_ONLY
    assert fi.payload is None


def test_filters_out_of_window():
    adapter = _adapter()
    entries = [
        _entry(title="In", video_id="inwindow000", pub_iso="2026-05-05T12:00:00Z"),
        _entry(title="Old", video_id="oldwindow00", pub_iso="2025-01-01T00:00:00Z"),
    ]
    with patch.object(yt_mod, "parse_feed_document", lambda url: _stub_feed(entries)), \
            patch.object(yt_mod, "fetch_transcript", lambda vid: None):
        items = list(adapter.fetch(WINDOW))
    assert {fi.item.title for fi in items} == {"In"}


def test_transcript_fetcher_exception_does_not_break_run():
    adapter = _adapter()
    entries = [_entry(title="Talk", video_id="boom1234567", summary="desc fallback")]

    def boom(_vid: str) -> str | None:
        raise RuntimeError("transcript service exploded")

    with patch.object(yt_mod, "parse_feed_document", lambda url: _stub_feed(entries)), \
            patch.object(yt_mod, "fetch_transcript", boom):
        items = list(adapter.fetch(WINDOW))

    assert len(items) == 1
    # transcript fetch failed → fall back to description (EXTRACT)
    assert items[0].item.payload_kind is PayloadKind.EXTRACT
    assert items[0].payload == "desc fallback"


def test_rejects_entry_without_channel_id_or_user():
    with pytest.raises(Exception, match="channel_id"):
        YoutubeAdapter(name="youtube", config={"channels": [{"default_author": "x"}]})


def test_rejects_malformed_channel_id():
    with pytest.raises(Exception, match="channel id"):
        YoutubeAdapter(name="youtube", config={"channels": [{"channel_id": "not-a-uc"}]})


def test_accepts_user_form():
    adapter = YoutubeAdapter(
        name="youtube",
        config={"channels": [{"user": "legacyuser", "default_author": "Legacy"}]},
    )
    assert adapter.channels[0]["url"].endswith("user=legacyuser")
