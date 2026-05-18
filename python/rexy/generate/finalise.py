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

Scored = tuple[Summarised, Scores]


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

    scored: list[Scored] = []
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
    scored = _enforce_mission_filter(scored, config)

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


def _enforce_mission_filter(scored: list[Scored], config: GeneratorConfig) -> list[Scored]:
    selected = list(scored[: config.final_size])
    remaining = list(scored[config.final_size:])

    while (
        _mission_count(selected, config) < config.min_sim_bridge_items
        or _agent_only_count(selected, config) > config.max_agent_only_items
    ):
        replacement_index = _first_mission_candidate_index(remaining, config)
        victim_index = _lowest_ranked_agent_only_index(selected, config)
        if replacement_index is None or victim_index is None:
            break

        selected[victim_index] = remaining.pop(replacement_index)
        selected.sort(key=lambda pair: pair[1].composite, reverse=True)

    return selected


def _mission_count(scored: list[Scored], config: GeneratorConfig) -> int:
    return sum(1 for pair in scored if _is_sim_core(pair, config) or _is_ai_sim_bridge(pair, config))


def _agent_only_count(scored: list[Scored], config: GeneratorConfig) -> int:
    return sum(1 for pair in scored if _is_agent_only(pair, config))


def _first_mission_candidate_index(scored: list[Scored], config: GeneratorConfig) -> int | None:
    for index, pair in enumerate(scored):
        if _is_sim_core(pair, config) or _is_ai_sim_bridge(pair, config):
            return index
    return None


def _lowest_ranked_agent_only_index(scored: list[Scored], config: GeneratorConfig) -> int | None:
    for index in range(len(scored) - 1, -1, -1):
        if _is_agent_only(scored[index], config):
            return index
    return None


def _is_agent_only(pair: Scored, config: GeneratorConfig) -> bool:
    topics = _normalised_topics(pair)
    return "agent" in topics and not _is_sim_core(pair, config) and not _is_ai_sim_bridge(pair, config)


def _is_sim_core(pair: Scored, config: GeneratorConfig) -> bool:
    return "simulation" in _normalised_topics(pair) or _has_keyword(pair, config.keywords_sim)


def _is_ai_sim_bridge(pair: Scored, config: GeneratorConfig) -> bool:
    return _has_keyword(pair, config.keywords_ai_sim_bridge)


def _normalised_topics(pair: Scored) -> set[str]:
    return {topic.strip().lower() for topic in pair[0].analysis.topics}


def _has_keyword(pair: Scored, keywords: tuple[str, ...]) -> bool:
    summarised = pair[0]
    item = summarised.pre_ranked.item
    analysis = summarised.analysis
    haystack = " ".join([
        item.title,
        item.author,
        item.type,
        " ".join(item.topics_raw),
        analysis.tldr_en,
        " ".join(analysis.takeaways_en),
        analysis.implication_en,
        " ".join(analysis.topics),
    ]).lower()
    return any(keyword.lower() in haystack for keyword in keywords)
