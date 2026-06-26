"""Top-level generator pipeline: corpus -> Selection -> gist Markdown.

Orchestrates the five stages from ADR-0004 and writes both artefacts in
lockstep per ADR-0002 (`Selection_<end>.jsonl` + `Weekly_Gist_<end>.md`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..corpus.items_store import ItemsStore
from ..corpus.payloads_store import PayloadsStore
from ..corpus.runs_store import RunsStore, make_run_id
from ..corpus.selections_store import SelectionsStore
from ..domain import SelectionEntry, Window, now_utc
from .config import GeneratorConfig
from .finalise import finalise
from .llm import LLMAnalyser
from .novelty import score_novelty
from .prefilter import prefilter
from .prerank import prerank
from .renderer import render_gist
from .summarise import summarise


@dataclass(slots=True)
class GenerationRun:
    run_id: str
    window: Window
    started_at: datetime
    finished_at: datetime | None = None
    items_in_corpus: int = 0
    items_after_prefilter: int = 0
    items_after_prerank: int = 0
    items_in_selection: int = 0
    selection_path: Path | None = None
    gist_path: Path | None = None

    def to_jsonable(self) -> dict:
        return {
            "kind": "generation",
            "run_id": self.run_id,
            "window": str(self.window),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at) if self.finished_at else None,
            "items_in_corpus": self.items_in_corpus,
            "items_after_prefilter": self.items_after_prefilter,
            "items_after_prerank": self.items_after_prerank,
            "items_in_selection": self.items_in_selection,
            "selection_path": str(self.selection_path) if self.selection_path else None,
            "gist_path": str(self.gist_path) if self.gist_path else None,
        }


def run_generation(
    window: Window,
    config: GeneratorConfig,
    analyser: LLMAnalyser,
    corpus_root: Path,
    gist_root: Path,
) -> GenerationRun:
    """Run the full pipeline; write Selection JSONL + Markdown gist + run file."""

    items_store = ItemsStore(corpus_root / "items.jsonl")
    payloads_store = PayloadsStore(corpus_root / "payloads")
    selections_store = SelectionsStore(corpus_root / "selections")
    runs_store = RunsStore(corpus_root / "runs")

    started = now_utc()
    run = GenerationRun(run_id=make_run_id(started), window=window, started_at=started)

    all_items = items_store.read_all()
    run.items_in_corpus = len(all_items)
    items_by_id = {it.id: it for it in all_items}

    filtered = prefilter(all_items, window, config, payloads_store)
    run.items_after_prefilter = len(filtered)

    shortlist = prerank(filtered, window, config, payloads_store)
    run.items_after_prerank = len(shortlist)

    summarised = summarise(shortlist, analyser, payloads_store)

    with_novelty = score_novelty(
        summarised, window, config, selections_store, items_by_id,
    )

    entries: list[SelectionEntry] = finalise(
        with_novelty, window, config,
        model=analyser.model, prompt_version=analyser.prompt_version,
    )
    run.items_in_selection = len(entries)

    selection_path = selections_store.write(window, entries)
    run.selection_path = selection_path

    gist_md = render_gist(window, entries, items_by_id)
    gist_root.mkdir(parents=True, exist_ok=True)
    gist_path = gist_root / f"Weekly_Gist_{window.end.isoformat()}.md"
    gist_path.write_text(gist_md, encoding="utf-8")
    run.gist_path = gist_path

    run.finished_at = now_utc()
    runs_store.root.mkdir(parents=True, exist_ok=True)
    (runs_store.root / f"Run_{run.run_id}.json").write_text(
        _dumps(run.to_jsonable()), encoding="utf-8",
    )
    return run


def _iso(dt: datetime) -> str:
    from datetime import timezone
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _dumps(d: dict) -> str:
    import json
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"
