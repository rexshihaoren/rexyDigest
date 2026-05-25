"""Publisher renderer tests.

Determinism is the key property — the same Selection in must produce the
same Markdown out, byte-for-byte. (No LLM noise per ADR-0007.)
"""

from datetime import date, datetime, timezone
from pathlib import Path

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.selections_store import SelectionsStore
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


def _item() -> Item:
    return Item(
        id="arxiv:1",
        source_type=SourceType.ARXIV,
        source_native_id="1",
        canonical_url="https://arxiv.org/abs/1",
        title="A breakthrough in agentic tool use",
        author="Lilian Weng",
        published_at=date(2026, 5, 5),
        type="paper",
        topics_raw=["cs.AI"],
        payload_kind=PayloadKind.METADATA_ONLY,
        payload_ref=None,
        fetched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
        adapter="test",
    )


def _entry(*, with_translations: bool = True) -> SelectionEntry:
    translations = Translations(
        title_zh="智能体工具使用的突破" if with_translations else None,
        tldr_zh="一项重要进展。" if with_translations else None,
        takeaways_zh=["要点 1", "要点 2", "要点 3"] if with_translations else None,
        implication_zh="对实践者很重要。" if with_translations else None,
        topics_zh=["智能体"] if with_translations else None,
    )
    return SelectionEntry(
        item_id="arxiv:1",
        window=WINDOW,
        rank=1,
        scores=Scores(relevance=4.5, novelty=4.0, actionability=3.5, composite=4.05),
        tldr_en="A major step forward.",
        takeaways_en=["Point 1", "Point 2", "Point 3"],
        implication_en="Matters for practitioners.",
        topics=["Agent"],
        translations=translations,
        model="m", prompt_version="v",
        generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
    )


class TestRenderer:
    def test_happy_path_includes_both_languages(self):
        md = render_public_brief(WINDOW, [_entry()], {"arxiv:1": _item()})
        assert "# AI×Simulation｜每周雷达" in md
        assert "## 智能体×世界模型｜本周严选：论文·视频·博文" in md
        assert "整理者：Rex Ren" in md
        assert "覆盖范围 Coverage window：**2026年05月03日 至 2026年05月10日**" in md
        assert "### 核心看点 Overview（双语）" in md
        assert "智能体工具使用的突破" in md
        assert "A breakthrough in agentic tool use" in md
        assert "一项重要进展。 ｜ A major step forward." in md
        assert "要点 1 ｜ Point 1" in md
        assert "**综合评分｜CompositeScore**" in md
        assert "4.1" in md or "4.0" in md  # composite formatted as 1dp

    def test_public_brief_renders_top_five_selection_entries_only(self):
        entries = []
        items = {}
        for i in range(1, 7):
            item = _item()
            item.id = f"arxiv:{i}"
            item.source_native_id = str(i)
            item.title = f"Title {i}"
            item.canonical_url = f"https://example.com/{i}"
            entry = _entry()
            entry.item_id = item.id
            entry.rank = i
            entry.translations.title_zh = f"标题 {i}"
            entries.append(entry)
            items[item.id] = item

        md = render_public_brief(WINDOW, entries, items)

        assert "入选 Items: **5**" in md
        assert "Title 5" in md
        assert "Title 6" not in md

    def test_public_brief_template_spec_tracks_renderer_contract(self):
        spec = (
            Path(__file__).resolve().parents[2] / "docs" / "templates" / "public_brief.md"
        ).read_text(encoding="utf-8")

        for marker in [
            "# AI×Simulation｜每周雷达",
            "## 智能体×世界模型｜本周严选：论文·视频·博文",
            "> 整理者：Rex Ren",
            "覆盖范围 Coverage window：**{start_date_zh} 至 {end_date_zh}** ｜ 入选 Items: **{item_count}**",
            "### 核心看点 Overview（双语）",
            "**标题｜Title**",
            "**来源｜Source**",
            "**摘要｜TL;DR**",
            "**要点｜Takeaways**",
            "**启示｜Implication**",
            "**综合评分｜CompositeScore**",
            "**主题｜Topics**",
            "**本周 KOL｜KOL roster**",
        ]:
            assert marker in spec

    def test_missing_translation_falls_back_to_english(self):
        md = render_public_brief(WINDOW, [_entry(with_translations=False)], {"arxiv:1": _item()})
        # CN side falls back to EN (transparent rather than fabricated)
        assert "A major step forward. ｜ A major step forward." in md
        assert "Matters for practitioners. ｜ Matters for practitioners." in md
        # When CN topics are missing, EN topics fill both sides — we don't fabricate Chinese
        assert "Agent ｜ Agent" in md

    def test_deterministic(self):
        item = _item()
        entry = _entry()
        a = render_public_brief(WINDOW, [entry], {"arxiv:1": item})
        b = render_public_brief(WINDOW, [entry], {"arxiv:1": item})
        assert a == b

    def test_unknown_item_is_skipped(self):
        # SelectionEntry references a missing Item — renderer should skip it,
        # not crash, since corpus inconsistency is real.
        e = _entry()
        e.item_id = "arxiv:does-not-exist"
        md = render_public_brief(WINDOW, [e], {})
        # Header still rendered, no entry body
        assert "AI×Simulation｜每周雷达" in md
        assert "**标题｜Title**" not in md


class TestEndToEndViaStore:
    def test_renders_selection_written_by_store(self, tmp_path: Path):
        items = ItemsStore(tmp_path / "items.jsonl")
        items.upsert_many([_item()])
        selections = SelectionsStore(tmp_path / "selections")
        selections.write(WINDOW, [_entry()])

        loaded_items = {it.id: it for it in items.read_all()}
        loaded_entries = selections.read(WINDOW)
        md = render_public_brief(WINDOW, loaded_entries, loaded_items)
        assert "智能体工具使用的突破" in md


class TestParity:
    def test_parity_ok_for_identical_briefs(self):
        from rexy.publish.parity import compare
        md = render_public_brief(WINDOW, [_entry()], {"arxiv:1": _item()})
        result = compare(md, md)
        assert result.ok, result.differences

    def test_parity_detects_missing_item(self):
        from rexy.publish.parity import compare
        md_full = render_public_brief(WINDOW, [_entry()], {"arxiv:1": _item()})
        md_empty = render_public_brief(WINDOW, [], {})
        result = compare(md_full, md_empty)
        assert not result.ok
        assert any("only in Node output" in d for d in result.differences)

    def test_parity_detects_score_drift(self):
        from rexy.publish.parity import compare
        item = _item()
        e1 = _entry()
        e2 = _entry()
        e2.scores = Scores(relevance=4.5, novelty=4.0, actionability=3.5, composite=2.0)
        md_a = render_public_brief(WINDOW, [e1], {"arxiv:1": item})
        md_b = render_public_brief(WINDOW, [e2], {"arxiv:1": item})
        result = compare(md_a, md_b)
        assert not result.ok
        assert any("composite" in d for d in result.differences)
