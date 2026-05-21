"""Provider-neutral model fallback wrapper."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from . import ItemAnalysis, ItemPrompt, LLMAnalyser


class ModelFallbackAnalyser:
    prompt_version: str

    def __init__(
        self,
        models: Sequence[str],
        build: Callable[[str], LLMAnalyser],
    ) -> None:
        self._models = [m for m in models if m]
        if not self._models:
            raise ValueError("ModelFallbackAnalyser needs at least one model")
        self._build = build
        first = build(self._models[0])
        self._first = first
        self.model = ",".join(self._models)
        self.prompt_version = first.prompt_version

    def analyse(self, prompt: ItemPrompt) -> ItemAnalysis:
        errors: list[str] = []
        for index, model in enumerate(self._models):
            analyser = self._first if index == 0 else self._build(model)
            try:
                return analyser.analyse(prompt)
            except RuntimeError as exc:
                errors.append(f"{model}: {exc}")
        raise RuntimeError(
            f"LLM analysis failed for {prompt.item_id} after {len(self._models)} model(s): "
            + " | ".join(errors)
        )
