"""End-to-end ingestion test using an in-memory adapter (no network).

This is the "in-memory adapter for testing" half of the ports & adapters
pattern from ADR-0003 — the framework is exercised end-to-end while the
real Source Adapter is replaced with a fixture.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.runs_store import RunsStore
from rexy.domain import (
    FetchedItem,
    Item,
    PayloadKind,
    SourceType,
    Window,
)
from rexy.ingest import run_ingestion
from rexy.sources._registry import ConfiguredAdapter


def _make_item(item_id: str, published_at: date, *, with_payload: bool = True) -> Item:
    return Item(
        id=item_id,
        source_type=SourceType.ARXIV,
        source_native_id=item_id.split(":", 1)[1],
        canonical_url=f"https://arxiv.org/abs/{item_id.split(':',1)[1]}",
        title=f"Item {item_id}",
        author="Tester",
        published_at=published_at,
        type="paper",
        topics_raw=["cs.AI"],
        payload_kind=PayloadKind.EXTRACT if with_payload else PayloadKind.METADATA_ONLY,
        payload_ref=None,
        fetched_at=datetime(2026, 5, 10, 12, tzinfo=timezone.utc),
        adapter="memtest",
    )


@dataclass
class _FixtureAdapter:
    name: str
    source_type: SourceType
    items: list[FetchedItem]

    def fetch(self, window: Window) -> Iterator[FetchedItem]:
        for fi in self.items:
            if window.contains(fi.item.published_at):
                yield fi


def _wrap(adapter: _FixtureAdapter) -> ConfiguredAdapter:
    return ConfiguredAdapter(
        name=adapter.name,
        source_type=adapter.source_type.value,
        config_sha="test-sha",
        adapter=adapter,
    )


def test_end_to_end_writes_corpus(tmp_path: Path):
    window = Window.parse("2026-05-03/2026-05-10")
    fixture = _FixtureAdapter(
        name="memtest",
        source_type=SourceType.ARXIV,
        items=[
            FetchedItem(item=_make_item("arxiv:2401.0001", date(2026, 5, 4)), payload="abstract one"),
            FetchedItem(item=_make_item("arxiv:2401.0002", date(2026, 5, 6)), payload="abstract two"),
        ],
    )

    run = run_ingestion([_wrap(fixture)], window, tmp_path)

    assert run.adapters[0].items_yielded == 2
    assert run.adapters[0].items_new == 2
    assert run.adapters[0].items_updated == 0
    assert run.adapters[0].errors == []
    assert (tmp_path / "items.jsonl").exists()
    assert (tmp_path / "payloads").is_dir()
    payload_files = list((tmp_path / "payloads").iterdir())
    assert len(payload_files) == 2
    items = ItemsStore(tmp_path / "items.jsonl").read_all()
    assert {it.id for it in items} == {"arxiv:2401.0001", "arxiv:2401.0002"}
    assert all(it.payload_ref for it in items)


def test_re_run_marks_existing_as_updated(tmp_path: Path):
    window = Window.parse("2026-05-03/2026-05-10")
    fixture = _FixtureAdapter(
        name="memtest",
        source_type=SourceType.ARXIV,
        items=[
            FetchedItem(item=_make_item("arxiv:2401.0001", date(2026, 5, 4)), payload="abstract one"),
        ],
    )
    run_ingestion([_wrap(fixture)], window, tmp_path)
    run2 = run_ingestion([_wrap(fixture)], window, tmp_path)
    assert run2.adapters[0].items_new == 0
    assert run2.adapters[0].items_updated == 1


def test_out_of_window_yield_is_recorded_as_error(tmp_path: Path):
    window = Window.parse("2026-05-03/2026-05-10")

    @dataclass
    class _CheatingAdapter:
        name: str = "cheater"
        source_type: SourceType = SourceType.ARXIV

        def fetch(self, w: Window) -> Iterator[FetchedItem]:
            # Misbehaving adapter: ignores `w` and yields out-of-window
            yield FetchedItem(
                item=_make_item("arxiv:9999.0001", date(2026, 1, 1)),
                payload="too old",
            )

    cheat = _CheatingAdapter()
    run = run_ingestion(
        [ConfiguredAdapter(name=cheat.name, source_type=cheat.source_type.value, config_sha="x", adapter=cheat)],
        window,
        tmp_path,
    )
    assert run.adapters[0].items_yielded == 0
    assert any("out-of-window" in err for err in run.adapters[0].errors)
    assert not (tmp_path / "items.jsonl").exists()


def test_metadata_only_item_no_payload_written(tmp_path: Path):
    window = Window.parse("2026-05-03/2026-05-10")
    fixture = _FixtureAdapter(
        name="memtest",
        source_type=SourceType.ARXIV,
        items=[
            FetchedItem(
                item=_make_item("arxiv:2401.0010", date(2026, 5, 5), with_payload=False),
                payload=None,
            ),
        ],
    )
    run = run_ingestion([_wrap(fixture)], window, tmp_path)

    assert run.adapters[0].items_yielded == 1
    assert run.adapters[0].errors == []
    assert (tmp_path / "items.jsonl").exists()
    assert not (tmp_path / "payloads").exists()  # nothing written
    items = ItemsStore(tmp_path / "items.jsonl").read_all()
    assert items[0].payload_kind is PayloadKind.METADATA_ONLY
    assert items[0].payload_ref is None


def test_run_file_records_window_and_stats(tmp_path: Path):
    window = Window.parse("2026-05-03/2026-05-10")
    fixture = _FixtureAdapter(
        name="memtest",
        source_type=SourceType.ARXIV,
        items=[
            FetchedItem(item=_make_item("arxiv:2401.0001", date(2026, 5, 4)), payload="x"),
        ],
    )
    run_ingestion([_wrap(fixture)], window, tmp_path)
    runs = RunsStore(tmp_path / "runs")
    assert runs.latest_window() == window
