"""deep_picks.toml loader + run_deep_notes integration."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.selections_store import SelectionsStore
from rexy.domain import Item, PayloadKind, Scores, SelectionEntry, SourceType, Translations, Window
from rexy.generate.deep_picks import load_deep_picks, picks_path
from rexy.generate.deep_notes import make_deep_note_writer, run_deep_notes


def test_load_deep_picks_ok(tmp_path: Path) -> None:
    p = tmp_path / "picks.toml"
    p.write_text('item_ids = ["a:1", "b:2"]\n', encoding="utf-8")
    assert load_deep_picks(p) == ["a:1", "b:2"]


def test_load_deep_picks_empty_list(tmp_path: Path) -> None:
    p = tmp_path / "picks.toml"
    p.write_text("item_ids = []\n", encoding="utf-8")
    assert load_deep_picks(p) == []


def test_load_deep_picks_rejects_three(tmp_path: Path) -> None:
    p = tmp_path / "picks.toml"
    p.write_text('item_ids = ["x", "y", "z"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="at most 2"):
        load_deep_picks(p)


def test_load_deep_picks_missing_key(tmp_path: Path) -> None:
    p = tmp_path / "picks.toml"
    p.write_text("other = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="item_ids"):
        load_deep_picks(p)


def _entry(item_id: str, window: Window) -> SelectionEntry:
    return SelectionEntry(
        item_id=item_id,
        window=window,
        rank=1,
        scores=Scores(relevance=4.0, novelty=3.0, actionability=4.0, composite=3.7),
        tldr_en="t",
        takeaways_en=["a"],
        implication_en="i",
        topics=["Agent"],
        translations=Translations(),
        model="m",
        prompt_version="v1",
        generated_at=datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
    )


def _item(item_id: str, payload_ref: str) -> Item:
    return Item(
        id=item_id,
        source_type=SourceType.RSS,
        source_native_id=None,
        canonical_url="https://example.com/p",
        title="Hello",
        author="A",
        published_at=date(2026, 1, 10),
        type="blog",
        topics_raw=[],
        payload_kind=PayloadKind.EXTRACT,
        payload_ref=payload_ref,
        fetched_at=datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
        adapter="rss",
    )


def test_run_deep_notes_memory_writes_one_file(tmp_path: Path) -> None:
    window = Window(start=date(2026, 1, 8), end=date(2026, 1, 15))
    corpus = tmp_path / "corpus"
    (corpus / "selections").mkdir(parents=True)
    (corpus / "payloads").mkdir(parents=True)
    ItemsStore(corpus / "items.jsonl").upsert_many([_item("rss:test1", "body.txt")])
    (corpus / "payloads" / "body.txt").write_text("payload body", encoding="utf-8")
    SelectionsStore(corpus / "selections").write(window, [_entry("rss:test1", window)])

    picks_root = tmp_path / "deep_picks"
    picks_root.mkdir()
    (picks_root / "2026-01-15.toml").write_text('item_ids = ["rss:test1"]\n', encoding="utf-8")

    inbox = tmp_path / "inbox"
    writer = make_deep_note_writer("memory", "ignored")
    run = run_deep_notes(window, corpus, picks_root, inbox, writer)
    assert len(run.written) == 1
    text = run.written[0].read_text(encoding="utf-8")
    assert "Hello" in text
    assert "rss:test1" in text
    assert "memory stub" in text


def test_run_deep_notes_rejects_id_not_in_selection(tmp_path: Path) -> None:
    window = Window(start=date(2026, 1, 8), end=date(2026, 1, 15))
    corpus = tmp_path / "corpus"
    (corpus / "selections").mkdir(parents=True)
    SelectionsStore(corpus / "selections").write(window, [_entry("rss:only", window)])

    picks_root = tmp_path / "deep_picks"
    picks_root.mkdir()
    (picks_root / "2026-01-15.toml").write_text('item_ids = ["rss:missing"]\n', encoding="utf-8")

    writer = make_deep_note_writer("memory", "x")
    with pytest.raises(ValueError, match="not in Selection"):
        run_deep_notes(window, corpus, picks_root, tmp_path / "inbox", writer)


def test_picks_path_matches_end_date() -> None:
    w = Window(start=date(2026, 1, 1), end=date(2026, 1, 8))
    assert picks_path(Path("/cfg"), w) == Path("/cfg/2026-01-08.toml")
