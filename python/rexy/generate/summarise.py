"""Stage 3 — Per-Item summarise + score + translate (LLM call).

For each shortlisted Item, builds an `ItemPrompt` from the Item + payload
and asks the `LLMAnalyser` to return an `ItemAnalysis`. Returns a list of
(Item, PreRanked, ItemAnalysis) tuples for the next stage.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..corpus.payloads_store import PayloadsStore
from ..domain import PayloadKind
from .llm import DEFAULT_LENS, ItemAnalysis, ItemPrompt, LLMAnalyser
from .prerank import PreRanked


@dataclass(slots=True)
class Summarised:
    pre_ranked: PreRanked
    analysis: ItemAnalysis


def summarise(
    shortlist: Iterable[PreRanked],
    analyser: LLMAnalyser,
    payloads: PayloadsStore,
    lens: str = DEFAULT_LENS,
) -> list[Summarised]:
    out: list[Summarised] = []
    for pr in shortlist:
        item = pr.item
        payload_text: str | None = None
        if item.payload_kind in (PayloadKind.EXTRACT, PayloadKind.FULL_TEXT) and item.payload_ref:
            try:
                payload_text = payloads.read(item.payload_ref)
            except FileNotFoundError:
                payload_text = None

        prompt = ItemPrompt(
            item_id=item.id,
            title=item.title,
            author=item.author,
            item_type=item.type,
            payload=payload_text,
            lens=lens,
        )
        analysis = analyser.analyse(prompt)
        out.append(Summarised(pre_ranked=pr, analysis=analysis))
    return out
