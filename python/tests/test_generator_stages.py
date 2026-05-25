"""Stage-by-stage tests for the Phase 2 generator.

Each stage is testable in isolation with hand-built fixtures so a regression
points at a single named stage rather than "the gist is wrong somehow".
"""

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.payloads_store import PayloadsStore
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
from rexy.generate.config import GeneratorConfig
from rexy.generate.finalise import finalise
from rexy.generate.llm import ItemAnalysis, ItemPrompt
from rexy.generate.llm.memory import InMemoryAnalyser
from rexy.generate.novelty import score_novelty
from rexy.generate.pipeline import run_generation
from rexy.generate.prefilter import prefilter
from rexy.generate.prerank import prerank
from rexy.generate.renderer import render_gist
from rexy.generate.summarise import summarise


# ---- helpers ----------------------------------------------------------------

def _item(
    id: str,
    title: str = "Agentic AI for tool use",
    author: str = "Random Person",
    published_at: date = date(2026, 5, 7),
    payload: str | None = "agent agent tool use abstract content",
    item_type: str = "paper",
) -> tuple[Item, str | None]:
    return (
        Item(
            id=id,
            source_type=SourceType.ARXIV,
            source_native_id=id.split(":", 1)[1],
            canonical_url=f"https://arxiv.org/abs/{id.split(':', 1)[1]}",
            title=title,
            author=author,
            published_at=published_at,
            type=item_type,
            topics_raw=["cs.AI"],
            payload_kind=PayloadKind.EXTRACT if payload else PayloadKind.METADATA_ONLY,
            payload_ref=f"{id.replace(':', '_')}.txt" if payload else None,
            fetched_at=datetime(2026, 5, 10, 12, tzinfo=timezone.utc),
            adapter="test",
        ),
        payload,
    )


def _populate(tmp_path: Path, items: list[tuple[Item, str | None]]) -> tuple[ItemsStore, PayloadsStore]:
    items_store = ItemsStore(tmp_path / "items.jsonl")
    payloads_store = PayloadsStore(tmp_path / "payloads")
    actual_items = []
    for item, payload in items:
        if payload is not None:
            ref = payloads_store.write(item.id, payload)
            item.payload_ref = ref
        actual_items.append(item)
    items_store.upsert_many(actual_items)
    return items_store, payloads_store


# ---- prefilter --------------------------------------------------------------

class TestPrefilter:
    def test_drops_out_of_window(self, tmp_path: Path):
        items, payloads = _populate(tmp_path, [
            _item("arxiv:1", published_at=date(2026, 5, 5)),
            _item("arxiv:2", published_at=date(2026, 1, 1)),
        ])
        kept = prefilter(items.read_all(), Window.parse("2026-05-03/2026-05-10"), GeneratorConfig(), payloads)
        assert {it.id for it in kept} == {"arxiv:1"}

    def test_drops_zero_keyword_hits(self, tmp_path: Path):
        items, payloads = _populate(tmp_path, [
            _item("arxiv:1", title="Quantum chromodynamics", payload="qcd is not relevant"),
            _item("arxiv:2", title="Agent for tool use", payload="agentic systems"),
        ])
        kept = prefilter(items.read_all(), Window.parse("2026-05-03/2026-05-10"), GeneratorConfig(), payloads)
        assert {it.id for it in kept} == {"arxiv:2"}

    def test_metadata_only_with_keyword_in_title_is_kept(self, tmp_path: Path):
        items, payloads = _populate(tmp_path, [
            _item("arxiv:1", title="Agent simulation hypothesis explained", payload=None),
        ])
        kept = prefilter(items.read_all(), Window.parse("2026-05-03/2026-05-10"), GeneratorConfig(), payloads)
        assert len(kept) == 1


# ---- prerank ----------------------------------------------------------------

class TestPrerank:
    def test_returns_at_most_shortlist_size(self, tmp_path: Path):
        items, payloads = _populate(tmp_path, [
            _item(f"arxiv:{i}", title=f"Agent paper {i}", published_at=date(2026, 5, 3 + (i % 8)))
            for i in range(60)
        ])
        cfg = GeneratorConfig(shortlist_size=15)
        ranked = prerank(items.read_all(), Window.parse("2026-05-03/2026-05-10"), cfg, payloads)
        assert len(ranked) == 15
        # Sorted descending
        scores = [r.score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_kol_prior_boosts_score(self, tmp_path: Path):
        items, payloads = _populate(tmp_path, [
            _item("arxiv:1", title="Agent for tool use", author="Lilian Weng"),
            _item("arxiv:2", title="Agent for tool use", author="Random Person"),
        ])
        ranked = prerank(items.read_all(), Window.parse("2026-05-03/2026-05-10"), GeneratorConfig(), payloads)
        ids_in_order = [r.item.id for r in ranked]
        assert ids_in_order[0] == "arxiv:1"  # KOL ranked higher


# ---- summarise --------------------------------------------------------------

class TestSummarise:
    def test_calls_analyser_with_payload(self, tmp_path: Path):
        items_store, payloads = _populate(tmp_path, [_item("arxiv:1", payload="my payload body")])
        from rexy.generate.prerank import PreRanked
        item = items_store.read_all()[0]
        seen: list[ItemPrompt] = []
        analyser = InMemoryAnalyser(analyse_fn=lambda p: (seen.append(p) or ItemAnalysis(
            item_id=p.item_id,
            relevance=4.0, actionability=3.0,
            tldr_en="ok", takeaways_en=["a"], implication_en="b", topics=["Agent"],
        )))
        out = summarise([PreRanked(item=item, score=1.0)], analyser, payloads)
        assert len(out) == 1
        assert out[0].analysis.relevance == 4.0
        assert seen[0].payload == "my payload body"
        assert seen[0].title == item.title


# ---- novelty ----------------------------------------------------------------

class TestNovelty:
    def test_overlapping_prior_selection_lowers_uniqueness(self, tmp_path: Path):
        # Set up a prior Selection with overlapping titles
        items, payloads = _populate(tmp_path, [
            _item("arxiv:new", title="Agent tool use breakthrough"),
            _item("arxiv:prior", title="Agent tool use overview", published_at=date(2026, 4, 28)),
        ])
        prior_window = Window.parse("2026-04-26/2026-05-03")
        selections = SelectionsStore(tmp_path / "selections")
        selections.write(prior_window, [
            SelectionEntry(
                item_id="arxiv:prior",
                window=prior_window,
                rank=1,
                scores=Scores(relevance=4, novelty=4, actionability=4, composite=4),
                tldr_en="prior", takeaways_en=[], implication_en="",
                topics=["Agent"],
                translations=Translations(),
                model="m", prompt_version="v",
                generated_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            )
        ])

        from rexy.generate.prerank import PreRanked
        from rexy.generate.summarise import Summarised
        all_items = items.read_all()
        items_by_id = {it.id: it for it in all_items}
        new_item = items_by_id["arxiv:new"]
        summarised = [Summarised(
            pre_ranked=PreRanked(item=new_item, score=1.0),
            analysis=ItemAnalysis(
                item_id="arxiv:new", relevance=4, actionability=4,
                tldr_en="x", takeaways_en=[], implication_en="", topics=["Agent"],
            ),
        )]
        out = score_novelty(
            summarised, Window.parse("2026-05-03/2026-05-10"), GeneratorConfig(),
            selections, items_by_id,
        )
        assert len(out) == 1
        novelty_with_overlap = out[0][1]

        # Now run without prior selection -> should be more novel
        empty_selections = SelectionsStore(tmp_path / "selections-empty")
        out2 = score_novelty(
            summarised, Window.parse("2026-05-03/2026-05-10"), GeneratorConfig(),
            empty_selections, items_by_id,
        )
        novelty_without_overlap = out2[0][1]
        assert novelty_without_overlap > novelty_with_overlap


# ---- finalise ---------------------------------------------------------------

class TestFinalise:
    def test_composite_formula_and_top_n(self):
        from rexy.generate.prerank import PreRanked
        from rexy.generate.summarise import Summarised
        cfg = GeneratorConfig(final_size=2)
        window = Window.parse("2026-05-03/2026-05-10")
        items_pr_an = [
            (Summarised(
                pre_ranked=PreRanked(
                    item=Item(
                        id=f"arxiv:{i}", source_type=SourceType.ARXIV, source_native_id=str(i),
                        canonical_url=f"https://x/{i}", title=f"t{i}", author="a",
                        published_at=date(2026, 5, 5), type="paper", topics_raw=[],
                        payload_kind=PayloadKind.METADATA_ONLY, payload_ref=None,
                        fetched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
                        adapter="test",
                    ),
                    score=1.0,
                ),
                analysis=ItemAnalysis(
                    item_id=f"arxiv:{i}",
                    relevance=relevance, actionability=actionability,
                    tldr_en="x", takeaways_en=[], implication_en="", topics=["Agent"],
                ),
            ), novelty)
            for i, relevance, actionability, novelty in [
                (1, 5.0, 5.0, 5.0),  # composite = 0.4*5 + 0.3*5 + 0.3*5 = 5.0
                (2, 1.0, 1.0, 1.0),  # composite = 1.0
                (3, 4.0, 4.0, 4.0),  # composite = 4.0
            ]
        ]
        out = finalise(items_pr_an, window, cfg, model="m", prompt_version="v")
        assert len(out) == 2
        assert [e.item_id for e in out] == ["arxiv:1", "arxiv:3"]
        assert out[0].rank == 1 and out[1].rank == 2
        assert out[0].scores.composite == 5.0
        assert out[1].scores.composite == 4.0

    def test_replaces_lowest_ranked_agent_only_item_to_meet_sim_bridge_floor(self):
        from rexy.generate.prerank import PreRanked
        from rexy.generate.summarise import Summarised

        def summarised(
            i: int,
            title: str,
            topics: list[str],
            relevance: float,
        ) -> tuple[Summarised, float]:
            return (
                Summarised(
                    pre_ranked=PreRanked(
                        item=Item(
                            id=f"arxiv:{i}", source_type=SourceType.ARXIV, source_native_id=str(i),
                            canonical_url=f"https://x/{i}", title=title, author="a",
                            published_at=date(2026, 5, 5), type="paper", topics_raw=[],
                            payload_kind=PayloadKind.METADATA_ONLY, payload_ref=None,
                            fetched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
                            adapter="test",
                        ),
                        score=1.0,
                    ),
                    analysis=ItemAnalysis(
                        item_id=f"arxiv:{i}",
                        relevance=relevance, actionability=relevance,
                        tldr_en="x", takeaways_en=[], implication_en="", topics=topics,
                    ),
                ),
                relevance,
            )

        cfg = GeneratorConfig(final_size=4, min_sim_bridge_items=2)
        window = Window.parse("2026-05-03/2026-05-10")
        out = finalise([
            summarised(1, "Agent orchestration", ["Agent"], 5.0),
            summarised(2, "Agent tool use", ["Agent"], 4.9),
            summarised(3, "Prompt router", ["Agent"], 4.8),
            summarised(4, "RAG benchmark", ["Agent"], 4.7),
            summarised(5, "Synthetic worlds for evaluation", ["Agent"], 4.6),
            summarised(6, "Simulation hypothesis evidence", ["Simulation"], 4.5),
        ], window, cfg, model="m", prompt_version="v")

        assert [e.item_id for e in out] == ["arxiv:1", "arxiv:2", "arxiv:5", "arxiv:6"]
        assert [e.rank for e in out] == [1, 2, 3, 4]

    def test_drops_low_relevance_mission_items_before_final_selection(self):
        from rexy.generate.prerank import PreRanked
        from rexy.generate.summarise import Summarised

        def summarised(
            i: int,
            title: str,
            topics: list[str],
            relevance: float,
            actionability: float,
        ) -> tuple[Summarised, float]:
            return (
                Summarised(
                    pre_ranked=PreRanked(
                        item=Item(
                            id=f"arxiv:{i}", source_type=SourceType.ARXIV, source_native_id=str(i),
                            canonical_url=f"https://x/{i}", title=title, author="a",
                            published_at=date(2026, 5, 5), type="paper", topics_raw=[],
                            payload_kind=PayloadKind.METADATA_ONLY, payload_ref=None,
                            fetched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
                            adapter="test",
                        ),
                        score=1.0,
                    ),
                    analysis=ItemAnalysis(
                        item_id=f"arxiv:{i}",
                        relevance=relevance, actionability=actionability,
                        tldr_en="x", takeaways_en=[], implication_en="", topics=topics,
                    ),
                ),
                5.0,
            )

        cfg = GeneratorConfig(final_size=3, min_sim_bridge_items=1, max_agent_only_items=3)
        window = Window.parse("2026-05-03/2026-05-10")
        out = finalise([
            summarised(1, "Agent orchestration", ["Agent"], 5.0, 5.0),
            summarised(2, "Agent tool use", ["Agent"], 4.9, 4.9),
            summarised(3, "Agent benchmark", ["Agent"], 4.8, 4.8),
            summarised(4, "Simulation-labelled irrelevant roundup", ["Simulation"], 1.2, 1.0),
        ], window, cfg, model="m", prompt_version="v")

        assert [e.item_id for e in out] == ["arxiv:1", "arxiv:2", "arxiv:3"]
        assert "arxiv:4" not in {e.item_id for e in out}


# ---- renderer ---------------------------------------------------------------

class TestRenderer:
    def test_output_matches_publisher_parser_contract(self):
        # Build one Item + one SelectionEntry, render, assert key regex hits.
        item, _ = _item("arxiv:1", title="Agent breakthrough", item_type="paper")
        item.payload_ref = None
        item.payload_kind = PayloadKind.METADATA_ONLY
        window = Window.parse("2026-05-03/2026-05-10")
        entry = SelectionEntry(
            item_id="arxiv:1", window=window, rank=1,
            scores=Scores(relevance=4.5, novelty=4.0, actionability=3.0, composite=3.9),
            tldr_en="A breakthrough.",
            takeaways_en=["Tools matter", "Agents learn", "Speed up"],
            implication_en="Use it.",
            topics=["Agent"],
            translations=Translations(),
            model="m", prompt_version="v",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )
        md = render_gist(window, [entry], {item.id: item})

        # Header
        assert "# Weekly Gist – 2026-05-10" in md
        assert "WEEKLY BRIEF" in md
        assert "COVERAGE_WINDOW: 2026-05-03 – 2026-05-10 | Items found 1 | Papers 1" in md

        # Item bullet matches publisher's topBullet regex
        import re
        bullet_re = re.compile(
            r"^\s*(?:\*\*)?(?:\d+\.\s+|\*\s+)(.+—\s+\d{4}-\d{2}-\d{2}\s+—\s+\[.*?\].*)(?:\*\*)?\s*$",
            re.MULTILINE,
        )
        assert bullet_re.search(md), "rendered item did not match publisher's topBullet regex"
        assert "**TL;DR:**" in md
        assert "**Takeaways:**" in md
        assert "**Implication for Rex Ren:**" in md
        assert "**CompositeScore (3.9) | Topics: Agent**" in md
        assert "| ItemID | KOL | Title |" in md
        assert "| arxiv:1 |" in md

    def test_weekly_gist_template_spec_tracks_renderer_contract(self):
        spec = (
            Path(__file__).resolve().parents[2] / "docs" / "templates" / "weekly_gist.md"
        ).read_text(encoding="utf-8")

        for marker in [
            "# Weekly Gist – {end_date}",
            "# WEEKLY BRIEF",
            "**COVERAGE_WINDOW:",
            "**TL;DR:**",
            "**Takeaways:**",
            "**Implication for Rex Ren:**",
            "**CompositeScore ({composite_score}) | Topics: {topics}**",
            "## Top Items for Rex Ren",
            "| ItemID | KOL | Title | Date | Topics | Type | Link | ReadPriority | ShortSummary | CompositeScore | Relevance | Novelty | Actionability |",
        ]:
            assert marker in spec


# ---- end-to-end -------------------------------------------------------------

class TestPipelineEndToEnd:
    def test_runs_with_in_memory_analyser(self, tmp_path: Path):
        items, _ = _populate(tmp_path, [
            _item("arxiv:1", title="Agentic tool use breakthrough", author="Lilian Weng",
                  payload="agent agent tool use breakthrough"),
            _item("arxiv:2", title="Multi-agent simulation hypothesis"),
            _item("arxiv:3", title="Quantum gravity", payload="qcd lorentz invariance only"),  # filtered out
        ])
        analyser = InMemoryAnalyser(analyse_fn=lambda p: ItemAnalysis(
            item_id=p.item_id, relevance=4.0, actionability=3.0,
            tldr_en=f"summary of {p.title[:40]}",
            takeaways_en=["A", "B", "C"], implication_en="Implication.",
            topics=["Agent"],
        ))
        gist_root = tmp_path / "gists"
        run = run_generation(
            window=Window.parse("2026-05-03/2026-05-10"),
            config=GeneratorConfig(),
            analyser=analyser,
            corpus_root=tmp_path,
            gist_root=gist_root,
        )
        assert run.items_in_corpus == 3
        assert run.items_after_prefilter == 2  # quantum gravity dropped
        assert run.items_in_selection == 2
        assert run.gist_path is not None and run.gist_path.exists()
        assert run.selection_path is not None and run.selection_path.exists()

        gist = run.gist_path.read_text(encoding="utf-8")
        assert "Items found 2" in gist
        assert "Lilian Weng" in gist  # KOL boosted to rank 1

        # Selection JSONL roundtrips via SelectionsStore
        loaded = SelectionsStore(tmp_path / "selections").read(Window.parse("2026-05-03/2026-05-10"))
        assert len(loaded) == 2
        assert loaded[0].rank == 1
