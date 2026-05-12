"""Stage 5 — Finalise: composite, sort, top-N, build Selection entries.

Materialises the per-Item LLM analyses and Python-derived novelty scores
into `SelectionEntry` records, sorted by composite score, capped at
`config.final_size`.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..domain import (
    Scores,
    SelectionEntry,
    Translations,
    Window,
    now_utc,
)
from .config import GeneratorConfig
from .summarise import Summarised


def finalise(
    summarised_with_novelty: Iterable[tuple[Summarised, float]],
    window: Window,
    config: GeneratorConfig,
    model: str,
    prompt_version: str,
) -> list[SelectionEntry]:
    """Build SelectionEntry list, ranked by composite score, top-N.

    Implementation note: we compute composite scores first, sort, slice to
    top-N, and only THEN build SelectionEntry objects. SelectionEntry's
    invariant requires rank >= 1, so we never construct one without a real
    rank.
    """

    scored: list[tuple[Summarised, Scores]] = []
    for s, novelty in summarised_with_novelty:
        a = s.analysis
        composite = round(
            config.weight_relevance * a.relevance
            + config.weight_novelty * novelty
            + config.weight_actionability * a.actionability,
            2,
        )
        scored.append((s, Scores(
            relevance=a.relevance,
            novelty=novelty,
            actionability=a.actionability,
            composite=composite,
        )))

    scored.sort(key=lambda pair: pair[1].composite, reverse=True)
    scored = scored[: config.final_size]

    generated_at = now_utc()
    out: list[SelectionEntry] = []
    for rank, (s, scores) in enumerate(scored, start=1):
        a = s.analysis
        out.append(SelectionEntry(
            item_id=a.item_id,
            window=window,
            rank=rank,
            scores=scores,
            tldr_en=a.tldr_en,
            takeaways_en=list(a.takeaways_en),
            implication_en=a.implication_en,
            topics=list(a.topics or []),
            translations=Translations(
                title_zh=a.title_zh,
                tldr_zh=a.tldr_zh,
                takeaways_zh=list(a.takeaways_zh) if a.takeaways_zh else None,
                implication_zh=a.implication_zh,
                topics_zh=list(a.topics_zh) if a.topics_zh else None,
            ),
            model=model,
            prompt_version=prompt_version,
            generated_at=generated_at,
        ))
    return out
