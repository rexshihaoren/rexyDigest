"""RssAdapter unit tests using a synthetic Atom feed.

`parse_feed_document` is patched to a stdlib-only stub so these tests pass
without the `feedparser` package (PEP 668 / bare `python3` CI). Production
still uses feedparser via `rss_adapter._default_parse_feed_document`.
"""

from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from rexy.domain import PayloadKind, SourceType, Window
from rexy.sources import rss_adapter as rss_adapter_mod
from rexy.sources.rss_adapter import RssAdapter, _canonicalise_url

_ATOM_URI = "http://www.w3.org/2005/Atom"
_ATOM_PREFIX = "a"


def _time_tuple_from_iso(s: str) -> tuple[int, ...]:
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    t = dt.astimezone(timezone.utc).timetuple()
    return (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_wday, t.tm_yday, 0)


def _parse_sample_atom_file(url: str) -> Any:
    """Minimal Atom → feedparser-like object for our synthetic fixtures only."""
    ns = {_ATOM_PREFIX: _ATOM_URI}
    path = Path(url)
    root = ET.parse(path).getroot()
    entries_out: list[dict[str, Any]] = []
    for ent in root.findall(f"{_ATOM_PREFIX}:entry", ns):
        title_el = ent.find(f"{_ATOM_PREFIX}:title", ns)
        title = (title_el.text or "").strip() if title_el is not None else ""

        link_href = ""
        for lk in ent.findall(f"{_ATOM_PREFIX}:link", ns):
            link_href = (lk.get("href") or "").strip()
            if link_href:
                break

        id_el = ent.find(f"{_ATOM_PREFIX}:id", ns)
        eid = (id_el.text or "").strip() if id_el is not None else ""

        pub_el = ent.find(f"{_ATOM_PREFIX}:published", ns)
        if pub_el is None:
            pub_el = ent.find(f"{_ATOM_PREFIX}:updated", ns)
        pub_text = (pub_el.text or "").strip() if pub_el is not None else ""
        published_parsed = _time_tuple_from_iso(pub_text) if pub_text else None

        sum_el = ent.find(f"{_ATOM_PREFIX}:summary", ns)
        summary: str | None = None
        if sum_el is not None and sum_el.text:
            summary = html.unescape(sum_el.text.strip())

        authors: list[dict[str, str]] = []
        for auth in ent.findall(f"{_ATOM_PREFIX}:author", ns):
            ne = auth.find(f"{_ATOM_PREFIX}:name", ns)
            if ne is not None and ne.text:
                authors.append({"name": ne.text.strip()})

        tags: list[SimpleNamespace] = []
        for cat in ent.findall(f"{_ATOM_PREFIX}:category", ns):
            term = cat.get("term")
            if term:
                tags.append(SimpleNamespace(term=term))

        d: dict[str, Any] = {
            "title": title,
            "link": link_href,
            "id": eid,
            "tags": tags,
            "authors": authors,
        }
        if published_parsed is not None:
            d["published_parsed"] = published_parsed
        if summary:
            d["summary"] = summary
        entries_out.append(d)

    return SimpleNamespace(entries=entries_out, bozo=False, bozo_exception=None)


_SAMPLE_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Feed</title>
  <link href="https://example.com/" rel="alternate"/>
  <id>https://example.com/</id>
  <updated>2026-05-08T12:00:00Z</updated>

  <entry>
    <title>An in-window post</title>
    <link href="https://example.com/post-1?utm_source=rss"/>
    <id>tag:example.com,2026:post-1</id>
    <published>2026-05-05T10:00:00Z</published>
    <updated>2026-05-05T10:00:00Z</updated>
    <author><name>Alice</name></author>
    <summary type="html">&lt;p&gt;A &lt;b&gt;summary&lt;/b&gt;.&lt;/p&gt;</summary>
    <category term="agents"/>
    <category term="LLM"/>
  </entry>

  <entry>
    <title>An old out-of-window post</title>
    <link href="https://example.com/post-old"/>
    <id>tag:example.com,2026:post-old</id>
    <published>2025-01-01T10:00:00Z</published>
    <author><name>Alice</name></author>
    <summary>old content</summary>
  </entry>

  <entry>
    <title>A metadata-only post</title>
    <link href="https://example.com/post-meta"/>
    <id>tag:example.com,2026:post-meta</id>
    <published>2026-05-06T10:00:00Z</published>
    <author><name>Alice</name></author>
  </entry>
</feed>
"""


def _adapter_with(tmp_path: Path) -> RssAdapter:
    feed_path = tmp_path / "feed.xml"
    feed_path.write_text(_SAMPLE_ATOM, encoding="utf-8")
    return RssAdapter(
        name="rss",
        config={"feeds": [{"url": str(feed_path), "type": "blog", "default_author": "Alice"}]},
    )


@patch.object(rss_adapter_mod, "parse_feed_document", _parse_sample_atom_file)
def test_filters_by_window_and_yields_extract(tmp_path: Path):
    adapter = _adapter_with(tmp_path)
    window = Window.parse("2026-05-03/2026-05-10")
    items = [fi for fi in adapter.fetch(window)]

    by_title = {fi.item.title: fi for fi in items}
    assert "An old out-of-window post" not in by_title
    assert "An in-window post" in by_title
    assert "A metadata-only post" in by_title

    in_window = by_title["An in-window post"]
    assert in_window.item.published_at == date(2026, 5, 5)
    assert in_window.item.payload_kind is PayloadKind.EXTRACT
    assert in_window.payload == "A summary ."  # html stripped, normalised whitespace
    assert in_window.item.canonical_url == "https://example.com/post-1"  # utm_ stripped
    assert "agents" in in_window.item.topics_raw
    assert in_window.item.author == "Alice"

    metadata_only = by_title["A metadata-only post"]
    assert metadata_only.item.payload_kind is PayloadKind.METADATA_ONLY
    assert metadata_only.payload is None


def test_canonicalise_strips_tracking_and_fragment():
    raw = "HTTPS://EXAMPLE.com/path/?utm_source=x&keep=1&fbclid=abc#section"
    assert _canonicalise_url(raw) == "https://example.com/path/?keep=1"


@patch.object(rss_adapter_mod, "parse_feed_document", _parse_sample_atom_file)
def test_url_shaped_guid_falls_back_to_url_sha1(tmp_path: Path):
    """Some feeds (Simon Willison etc.) put a URL in <id>; we don't want
    those URLs becoming the Item's source_native_id (produces 100+ char IDs)."""
    feed = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>F</title><id>https://x/</id><updated>2026-05-08T00:00:00Z</updated>
  <entry>
    <title>P</title>
    <link href="https://x.example/post"/>
    <id>https://x.example/post#atom-everything</id>
    <published>2026-05-05T00:00:00Z</published>
  </entry>
</feed>
"""
    feed_path = tmp_path / "feed.xml"
    feed_path.write_text(feed, encoding="utf-8")
    adapter = RssAdapter(name="rss", config={"feeds": [{"url": str(feed_path), "type": "blog"}]})
    items = [fi for fi in adapter.fetch(Window.parse("2026-05-03/2026-05-10"))]
    assert len(items) == 1
    assert items[0].item.id.startswith("url-sha1:")
    assert items[0].item.source_native_id is None


def test_invalid_feed_type_rejected(tmp_path: Path):
    feed_path = tmp_path / "feed.xml"
    feed_path.write_text(_SAMPLE_ATOM, encoding="utf-8")
    with pytest.raises(Exception, match="rocket|not in"):
        RssAdapter(
            name="rss",
            config={"feeds": [{"url": str(feed_path), "type": "rocket"}]},
        )


def test_empty_feeds_list_rejected():
    with pytest.raises(Exception, match="non-empty `feeds` list"):
        RssAdapter(name="rss", config={"feeds": []})
