"""Stage 2 — Pre-rank shortlist (deterministic Python).

Cheap signal-based ranking that produces a top-N shortlist for the LLM
to score. Per ADR-0004 we want this to be:

  pre_rank_score = recency * kol_prior * keyword_density

Recency: 1.0 at the Window end, decaying linearly to 0.5 at the Window start.
KOL prior: 1.0 by default; configured boosts >1 for known KOLs (substring
match, case-insensitive against `Item.author`).
Keyword density: 1 + log(1 + hits_per_100_chars), so an Item with 0 hits is
already filtered (in prefilter), and gains diminish.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from ..corpus.payloads_store import PayloadsStore
from ..domain import Item, PayloadKind, Window
from .config import GeneratorConfig


@dataclass(slots=True, frozen=True)
class PreRanked:
    item: Item
    score: float


def prerank(
    items: Iterable[Item],
    window: Window,
    config: GeneratorConfig,
    payloads: PayloadsStore,
) -> list[PreRanked]:
    """Score, sort descending, take top `config.shortlist_size`."""

    keywords = [kw.lower() for kw in config.all_keywords]
    span_days = max((window.end - window.start).days, 1)
    scored: list[PreRanked] = []

    for item in items:
        days_from_end = max((window.end - item.published_at).days, 0)
        recency = 1.0 - 0.5 * (days_from_end / span_days)

        author_lc = (item.author or "").lower()
        kol_prior = 1.0
        for kol, weight in config.kol_priors.items():
            if kol in author_lc:
                kol_prior = max(kol_prior, weight)

        haystack_len, hits = _count_hits(item, keywords, payloads)
        per_100 = (hits * 100.0) / max(haystack_len, 1)
        keyword_density = 1.0 + math.log1p(per_100)

        score = recency * kol_prior * keyword_density
        scored.append(PreRanked(item=item, score=score))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[: config.shortlist_size]


def _count_hits(
    item: Item, keywords: list[str], payloads: PayloadsStore,
) -> tuple[int, int]:
    parts = [item.title.lower(), " ".join(item.topics_raw).lower()]
    if item.payload_kind in (PayloadKind.EXTRACT, PayloadKind.FULL_TEXT) and item.payload_ref:
        try:
            parts.append(payloads.read(item.payload_ref).lower())
        except FileNotFoundError:
            pass
    haystack = "\n".join(parts)
    hits = sum(haystack.count(kw) for kw in keywords)
    return len(haystack), hits
