"""InMemoryAnalyser — deterministic LLM stand-in for tests.

Two construction modes:
  - Fixture map: pass `analyses={"item_id": ItemAnalysis(...), ...}`.
    Items not in the map get a default low-score analysis.
  - Callable: pass `analyse_fn=lambda prompt: ItemAnalysis(...)`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from . import ItemAnalysis, ItemPrompt


class InMemoryAnalyser:
    model: str = "in-memory-test"
    prompt_version: str = "test-v0"

    def __init__(
        self,
        analyses: Mapping[str, ItemAnalysis] | None = None,
        analyse_fn: Callable[[ItemPrompt], ItemAnalysis] | None = None,
        model: str = "in-memory-test",
        prompt_version: str = "test-v0",
    ) -> None:
        if (analyses is None) == (analyse_fn is None):
            raise ValueError("InMemoryAnalyser needs exactly one of `analyses` or `analyse_fn`")
        self._analyses = dict(analyses) if analyses else None
        self._analyse_fn = analyse_fn
        self.model = model
        self.prompt_version = prompt_version

    def analyse(self, prompt: ItemPrompt) -> ItemAnalysis:
        if self._analyses is not None:
            if prompt.item_id in self._analyses:
                return self._analyses[prompt.item_id]
            return ItemAnalysis(
                item_id=prompt.item_id,
                relevance=1.0,
                actionability=1.0,
                tldr_en=f"(no fixture for {prompt.item_id})",
                takeaways_en=[],
                implication_en="",
                topics=[],
            )
        assert self._analyse_fn is not None
        return self._analyse_fn(prompt)
