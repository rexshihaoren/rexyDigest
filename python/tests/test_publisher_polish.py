"""Publisher polish — Top 3 overview and deterministic rendering.

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


def _entry(
    item_id: str,
    *,
    rank: int,
    composite: float = 4.5,
    topics: list[str] | None = None,
    tldr: str = "What you should know.",
) -> SelectionEntry:
    return SelectionEntry(
        item_id=item_id,
        window=WINDOW,
        rank=rank,
        scores=Scores(relevance=4.5, novelty=4.0, actionability=4.0, composite=composite),
        tldr_en=tldr,
        takeaways_en=["a", "b", "c"],
        implication_en="It matters.",
        topics=topics or ["Agent"],
        translations=Translations(
            title_zh=f"标题 {item_id}",
            tldr_zh="要点摘要。",
            takeaways_zh=["一", "二", "三"],
            implication_zh="重要。",
            topics_zh=["智能体"] if topics != ["Simulation"] else ["模拟"],
        ),
        model="m",
        prompt_version="v",
        generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
    )


def test_overview_prefers_mission_bridge_then_composite():
    items = {
        "youtube:a": _item("youtube:a", author="A"),
        "youtube:b": _item("youtube:b", author="B"),
        "youtube:c": _item("youtube:c", author="C"),
        "youtube:d": _item("youtube:d", author="D"),
    }
    entries = [
        _entry("youtube:a", rank=1, composite=5.0),
        _entry("youtube:b", rank=2, composite=4.1, topics=["Simulation"]),
        _entry("youtube:c", rank=3, composite=4.9, tldr="Synthetic worlds improve evals."),
        _entry("youtube:d", rank=4, composite=4.8),
    ]
    md = render_public_brief(WINDOW, entries, items)

    assert "### 核心看点 Overview（双语）" in md
    assert "- 🏅 标题 youtube:c ｜ Title youtube:c" in md
    assert "- 🏅 标题 youtube:b ｜ Title youtube:b" in md
    assert "- 🏅 标题 youtube:a ｜ Title youtube:a" in md
    assert "Top #1" not in md


def test_overview_only_uses_items_rendered_in_public_top_five():
    items = {
        "youtube:a": _item("youtube:a", author="A"),
        "youtube:b": _item("youtube:b", author="B"),
        "youtube:c": _item("youtube:c", author="C"),
        "youtube:d": _item("youtube:d", author="D"),
        "youtube:e": _item("youtube:e", author="E"),
        "youtube:f": _item("youtube:f", author="F"),
    }
    entries = [
        _entry("youtube:a", rank=1, composite=5.0),
        _entry("youtube:b", rank=2, composite=4.9),
        _entry("youtube:c", rank=3, composite=4.8),
        _entry("youtube:d", rank=4, composite=4.7),
        _entry("youtube:e", rank=5, composite=4.6),
        _entry("youtube:f", rank=6, composite=5.0, topics=["Simulation"]),
    ]

    md = render_public_brief(WINDOW, entries, items)

    assert "Title youtube:f" not in md
    assert "- 🏅 标题 youtube:f ｜ Title youtube:f" not in md


def test_public_brief_suppresses_internal_kol_markers():
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
    assert "KOL roster" not in md
    assert "本周 KOL" not in md
    assert "karpathy" not in md
    assert "lilian weng" not in md


def test_no_kol_roster_when_no_kol_markers():
    items = {"x:1": _item("x:1", author="Anon")}
    entries = [_entry("x:1", rank=1)]
    md = render_public_brief(WINDOW, entries, items)
    assert "KOL roster" not in md
    assert "### 核心看点 Overview（双语）" in md


def test_renderer_remains_deterministic_with_lead():
    items = {"youtube:a": _item("youtube:a", author="A", topics=["kol:karpathy"])}
    entries = [_entry("youtube:a", rank=1, composite=4.5)]
    a = render_public_brief(WINDOW, entries, items)
    b = render_public_brief(WINDOW, entries, items)
    assert a == b
