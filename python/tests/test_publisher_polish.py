"""Publisher polish — 本周亮点 lead block and KOL roster footer.

Both additions are deterministic; we re-render twice to assert byte-equality.
"""

from datetime import date, datetime, timezone

from rexy.domain import (
    Item,
    PayloadKind,
    Scores,
    SelectionEntry,
    SourceType,
    Translations,
    Window,
)
from rexy.publish.renderer import render_public_brief


WINDOW = Window.parse("2026-05-03/2026-05-10")


def _item(item_id: str, *, author: str, topics: list[str] | None = None) -> Item:
    return Item(
        id=item_id,
        source_type=SourceType.YOUTUBE,
        source_native_id=item_id.split(":", 1)[1],
        canonical_url=f"https://example.com/{item_id}",
        title=f"Title {item_id}",
        author=author,
        published_at=date(2026, 5, 6),
        type="video",
        topics_raw=topics or [],
        payload_kind=PayloadKind.METADATA_ONLY,
        payload_ref=None,
        fetched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
        adapter="youtube",
    )


def _entry(item_id: str, *, rank: int, composite: float = 4.5) -> SelectionEntry:
    return SelectionEntry(
        item_id=item_id,
        window=WINDOW,
        rank=rank,
        scores=Scores(relevance=4.5, novelty=4.0, actionability=4.0, composite=composite),
        tldr_en="What you should know.",
        takeaways_en=["a", "b", "c"],
        implication_en="It matters.",
        topics=["Agent"],
        translations=Translations(
            title_zh=f"标题 {item_id}",
            tldr_zh="要点摘要。",
            takeaways_zh=["一", "二", "三"],
            implication_zh="重要。",
            topics_zh=["智能体"],
        ),
        model="m",
        prompt_version="v",
        generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
    )


def test_lead_block_uses_rank_1():
    items = {
        "youtube:a": _item("youtube:a", author="Karpathy", topics=["kol:karpathy"]),
        "youtube:b": _item("youtube:b", author="Random"),
    }
    entries = [_entry("youtube:b", rank=2, composite=3.0),
               _entry("youtube:a", rank=1, composite=4.8)]
    md = render_public_brief(WINDOW, entries, items)
    assert "**本周亮点｜Lead**" in md
    assert "标题 youtube:a" in md  # rank-1 title shown in lead
    assert "综合评分｜CompositeScore: 4.8" in md


def test_kol_roster_lists_unique_slugs_in_rank_order():
    items = {
        "youtube:a": _item("youtube:a", author="A", topics=["kol:karpathy"]),
        "youtube:b": _item("youtube:b", author="B", topics=["kol:lilian weng"]),
        "youtube:c": _item("youtube:c", author="C", topics=["kol:karpathy"]),  # dup
    }
    entries = [
        _entry("youtube:a", rank=1, composite=4.5),
        _entry("youtube:b", rank=2, composite=4.2),
        _entry("youtube:c", rank=3, composite=4.0),
    ]
    md = render_public_brief(WINDOW, entries, items)
    assert "**本周 KOL｜KOL roster**: karpathy, lilian weng" in md


def test_no_kol_roster_when_no_kol_markers():
    items = {"x:1": _item("x:1", author="Anon")}
    entries = [_entry("x:1", rank=1)]
    md = render_public_brief(WINDOW, entries, items)
    assert "KOL roster" not in md
    # Lead block still rendered (KOL roster is optional)
    assert "**本周亮点｜Lead**" in md


def test_renderer_remains_deterministic_with_lead_and_roster():
    items = {"youtube:a": _item("youtube:a", author="A", topics=["kol:karpathy"])}
    entries = [_entry("youtube:a", rank=1, composite=4.5)]
    a = render_public_brief(WINDOW, entries, items)
    b = render_public_brief(WINDOW, entries, items)
    assert a == b
