"""Stage 4 — Novelty score (deterministic Python, Corpus-aware).

For each summarised Item, score how novel it is given recent prior
Selections. The signal we use is intentionally simple — title + topics
token overlap — because per ADR-0004 we explicitly defer embedding-based
similarity until quality demands it.

Score formula:
  novelty = recency_factor * uniqueness_factor

  recency_factor   = 1.0 if Item published in current Window
                   = 0.5 if it slipped in late but is still a few weeks old
  uniqueness_factor = 1.0 - max_similarity_to_prior_selections
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from ..corpus.selections_store import SelectionsStore
from ..domain import Item, SelectionEntry, Window
from .config import GeneratorConfig
from .summarise import Summarised


def score_novelty(
    summarised: Iterable[Summarised],
    window: Window,
    config: GeneratorConfig,
    selections: SelectionsStore,
    items_by_id: dict[str, Item],
) -> list[tuple[Summarised, float]]:
    """Return (summarised, novelty_score) tuples; score in [0.0, 5.0]."""

    prior_titles = _collect_prior_titles(window, config, selections, items_by_id)
    span_days = max((window.end - window.start).days, 1)

    scored: list[tuple[Summarised, float]] = []
    for s in summarised:
        item = s.pre_ranked.item

        days_off_window = max(0, (window.start - item.published_at).days)
        if days_off_window == 0:
            recency_factor = 1.0
        else:
            recency_factor = max(0.5, 1.0 - 0.1 * (days_off_window / span_days))

        own_tokens = _tokens(item.title)
        max_sim = 0.0
        for prior_tokens in prior_titles:
            sim = _jaccard(own_tokens, prior_tokens)
            if sim > max_sim:
                max_sim = sim

        uniqueness = max(0.0, 1.0 - max_sim)
        # Map to 1.0-5.0 range to be on-scale with relevance/actionability.
        scaled = 1.0 + 4.0 * recency_factor * uniqueness
        scored.append((s, round(scaled, 2)))

    return scored


def _collect_prior_titles(
    window: Window,
    config: GeneratorConfig,
    selections: SelectionsStore,
    items_by_id: dict[str, Item],
) -> list[set[str]]:
    """Tokenise titles of every Item picked in any Selection within the lookback."""
    cutoff = window.start - timedelta(weeks=config.novelty_lookback_weeks)
    prior_titles: list[set[str]] = []

    if not selections.root.exists():
        return prior_titles

    for path in selections.root.glob("Selection_*.jsonl"):
        # Selection_<end>.jsonl — parse end date from filename
        try:
            end_str = path.stem.split("_", 1)[1]
            end = date.fromisoformat(end_str)
        except (ValueError, IndexError):
            continue
        if end < cutoff or end >= window.end:
            continue
        try:
            entries = _read_entries(path)
        except (OSError, ValueError):
            continue
        for entry in entries:
            item = items_by_id.get(entry.item_id)
            if item is not None:
                prior_titles.append(_tokens(item.title))
    return prior_titles


def _read_entries(path) -> list[SelectionEntry]:
    """Parse a Selection_*.jsonl by hand (avoids importing SelectionsStore.read,
    which expects a Window and re-derives the same path)."""
    import json
    out: list[SelectionEntry] = []
    with path.open("r", encoding="utf-8") as fp:
        for raw in fp:
            raw = raw.strip()
            if not raw:
                continue
            out.append(SelectionEntry.from_jsonable(json.loads(raw)))
    return out


def _tokens(text: str) -> set[str]:
    import re
    return {t for t in re.split(r"\W+", text.lower()) if len(t) > 3}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
