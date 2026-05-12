"""Items / Payloads / Runs stores: schema conformance + atomic-write happy paths."""

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.payloads_store import PayloadsStore
from rexy.corpus.runs_store import (
    AdapterRunStat,
    IngestionRun,
    RunsStore,
    make_run_id,
)
from rexy.domain import Item, PayloadKind, SourceType, Window


def _make_item(item_id: str, *, payload_ref: str | None = "x.txt"):
    kind = PayloadKind.EXTRACT if payload_ref else PayloadKind.METADATA_ONLY
    return Item(
        id=item_id,
        source_type=SourceType.ARXIV,
        source_native_id=item_id.split(":", 1)[1],
        canonical_url=f"https://arxiv.org/abs/{item_id.split(':',1)[1]}",
        title=f"Paper {item_id}",
        author="Test",
        published_at=date(2026, 5, 7),
        type="paper",
        topics_raw=["cs.AI"],
        payload_kind=kind,
        payload_ref=payload_ref,
        fetched_at=datetime(2026, 5, 10, 12, tzinfo=timezone.utc),
        adapter="arxiv",
    )


class TestItemsStore:
    def test_upsert_writes_and_reads(self, tmp_path: Path):
        store = ItemsStore(tmp_path / "items.jsonl")
        added, updated = store.upsert_many([
            _make_item("arxiv:2401.0001"),
            _make_item("arxiv:2401.0002"),
        ])
        assert (added, updated) == (2, 0)
        assert {it.id for it in store.read_all()} == {"arxiv:2401.0001", "arxiv:2401.0002"}

    def test_upsert_updates_existing(self, tmp_path: Path):
        store = ItemsStore(tmp_path / "items.jsonl")
        store.upsert_many([_make_item("arxiv:2401.0001")])
        added, updated = store.upsert_many([_make_item("arxiv:2401.0001")])
        assert (added, updated) == (0, 1)
        assert len(store.read_all()) == 1

    def test_round_trip_preserves_all_fields(self, tmp_path: Path):
        store = ItemsStore(tmp_path / "items.jsonl")
        original = _make_item("arxiv:2401.0001")
        store.upsert_many([original])
        loaded = store.read_all()[0]
        assert loaded.to_jsonable() == original.to_jsonable()

    def test_malformed_line_is_diagnostic(self, tmp_path: Path):
        path = tmp_path / "items.jsonl"
        path.write_text('{"id": "broken"}\n', encoding="utf-8")
        store = ItemsStore(path)
        with pytest.raises(ValueError, match=":1:"):
            store.read_all()

    def test_upsert_is_atomic_no_partial_file_on_crash(self, tmp_path: Path, monkeypatch):
        store = ItemsStore(tmp_path / "items.jsonl")
        store.upsert_many([_make_item("arxiv:2401.0001")])
        original = (tmp_path / "items.jsonl").read_text(encoding="utf-8")

        # Force replace() to fail mid-flight; original file must survive.
        def boom(*a, **kw):
            raise OSError("simulated disk error")
        monkeypatch.setattr(Path, "replace", boom)

        with pytest.raises(OSError):
            store.upsert_many([_make_item("arxiv:2401.0002")])
        assert (tmp_path / "items.jsonl").read_text(encoding="utf-8") == original


class TestPayloadsStore:
    def test_namespaced_id_becomes_safe_filename(self, tmp_path: Path):
        store = PayloadsStore(tmp_path)
        ref = store.write("arxiv:2401.12345", "abstract text")
        assert ref == "arxiv_2401.12345.txt"
        assert store.read(ref) == "abstract text"

    def test_unicode_payload_roundtrips(self, tmp_path: Path):
        store = PayloadsStore(tmp_path)
        ref = store.write("rss:abc", "中文内容 — 你好")
        assert store.read(ref) == "中文内容 — 你好"

    def test_url_chars_are_sanitised(self, tmp_path: Path):
        store = PayloadsStore(tmp_path)
        ref = store.write("rss:https://x.example/post#frag?q=1", "body")
        assert "#" not in ref
        assert "?" not in ref
        assert "/" not in ref
        # Only filesystem-safe chars (and the dot for the suffix)
        import re
        assert re.fullmatch(r"[A-Za-z0-9._-]+", ref)
        assert store.read(ref) == "body"

    def test_long_id_is_truncated_with_hash(self, tmp_path: Path):
        store = PayloadsStore(tmp_path)
        long_id = "rss:" + ("a" * 500)
        ref = store.write(long_id, "body")
        assert len(ref) <= 200
        # Different long IDs that share a prefix still produce distinct files
        ref2 = store.write(long_id + "-different-suffix", "body2")
        assert ref != ref2


class TestRunsStore:
    def test_writes_and_finds_latest_window(self, tmp_path: Path):
        store = RunsStore(tmp_path)
        run = IngestionRun(
            run_id=make_run_id(datetime(2026, 5, 10, 13, tzinfo=timezone.utc)),
            window=Window.parse("2026-05-03/2026-05-10"),
            started_at=datetime(2026, 5, 10, 13, tzinfo=timezone.utc),
            finished_at=datetime(2026, 5, 10, 13, 1, tzinfo=timezone.utc),
            adapters=[
                AdapterRunStat(name="arxiv", config_sha="aa", items_yielded=3, items_new=3),
            ],
        )
        path = store.write(run)
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        assert on_disk["kind"] == "ingestion"
        assert on_disk["window"] == "2026-05-03/2026-05-10"
        assert on_disk["adapters"][0]["items_yielded"] == 3
        assert store.latest_window() == Window.parse("2026-05-03/2026-05-10")

    def test_latest_window_picks_newest_run_id(self, tmp_path: Path):
        store = RunsStore(tmp_path)
        for run_id, win in [
            ("20260503T000000Z", "2026-04-26/2026-05-03"),
            ("20260510T000000Z", "2026-05-03/2026-05-10"),
            ("20260417T000000Z", "2026-04-10/2026-04-17"),
        ]:
            store.write(IngestionRun(
                run_id=run_id,
                window=Window.parse(win),
                started_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                finished_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            ))
        assert store.latest_window() == Window.parse("2026-05-03/2026-05-10")

    def test_latest_window_none_when_empty(self, tmp_path: Path):
        store = RunsStore(tmp_path / "missing")
        assert store.latest_window() is None
