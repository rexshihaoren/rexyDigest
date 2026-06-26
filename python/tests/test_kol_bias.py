"""KOL bias: topic-marker bypass at prefilter and boost at prerank.

Author-substring bias is already covered by `test_generator_stages`.
Here we exercise the additional **`kol:<slug>`** topic-marker path.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.payloads_store import PayloadsStore
from rexy.domain import Item, PayloadKind, SourceType, Window
from rexy.generate.config import GeneratorConfig
from rexy.generate.prefilter import prefilter
from rexy.generate.prerank import prerank


def _build_item(
    item_id: str,
    *,
    title: str,
    author: str,
    topics: list[str],
    payload: str | None,
) -> Item:
    return Item(
        id=item_id,
        source_type=SourceType.YOUTUBE,
        source_native_id=item_id.split(":", 1)[1],
        canonical_url=f"https://example.com/{item_id}",
        title=title,
        author=author,
        published_at=date(2026, 5, 6),
        type="video",
        topics_raw=topics,
        payload_kind=PayloadKind.EXTRACT if payload else PayloadKind.METADATA_ONLY,
        payload_ref=f"{item_id.replace(':', '_')}.txt" if payload else None,
        fetched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
        adapter="youtube",
    )


def _populate(tmp: Path, items: list[tuple[Item, str | None]]) -> tuple[ItemsStore, PayloadsStore]:
    items_store = ItemsStore(tmp / "items.jsonl")
    payloads = PayloadsStore(tmp / "payloads")
    for item, payload in items:
        if payload is not None:
            ref = payloads.write(item.id, payload)
            item.payload_ref = ref
    items_store.upsert_many([it for it, _ in items])
    return items_store, payloads


def test_kol_topic_marker_bypasses_keyword_filter(tmp_path: Path):
    """Item with `kol:<slug>` should survive prefilter even with 0 keyword hits."""

    kol_item = _build_item(
        "youtube:kol1",
        title="A cooking show",  # zero AGENT/SIM keyword hits
        author="Random Person",
        topics=["kol:karpathy"],  # matches configured KOL prior
        payload="totally off topic content",
    )
    non_kol = _build_item(
        "youtube:other",
        title="A cooking show",
        author="Random Person",
        topics=["food"],
        payload="totally off topic content",
    )
    store, payloads = _populate(tmp_path, [(kol_item, "off"), (non_kol, "off")])

    kept = prefilter(
        store.read_all(),
        Window.parse("2026-05-03/2026-05-10"),
        GeneratorConfig(),
        payloads,
    )
    kept_ids = {it.id for it in kept}
    assert "youtube:kol1" in kept_ids
    assert "youtube:other" not in kept_ids


def test_kol_topic_marker_boosts_prerank_over_non_kol(tmp_path: Path):
    """Same title + payload → KOL-tagged item ranks higher."""

    kol_item = _build_item(
        "youtube:kol1",
        title="Agent talk",
        author="No-Match Author",   # author substring won't hit kol_priors
        topics=["kol:karpathy"],
        payload="agent agent tool use",
    )
    non_kol = _build_item(
        "youtube:other",
        title="Agent talk",
        author="No-Match Author",
        topics=["tech"],
        payload="agent agent tool use",
    )
    store, payloads = _populate(tmp_path, [(kol_item, "agent agent tool use"),
                                            (non_kol, "agent agent tool use")])

    ranked = prerank(
        store.read_all(),
        Window.parse("2026-05-03/2026-05-10"),
        GeneratorConfig(),
        payloads,
    )
    ids_in_order = [r.item.id for r in ranked]
    assert ids_in_order[0] == "youtube:kol1"
