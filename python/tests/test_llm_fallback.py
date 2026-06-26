"""Provider-neutral model fallback behavior."""

from __future__ import annotations

import pytest

from rexy.generate.llm import ItemAnalysis, ItemPrompt
from rexy.generate.llm.fallback import ModelFallbackAnalyser


class _Analyser:
    prompt_version = "test-v0"

    def __init__(self, model: str, fail: bool) -> None:
        self.model = model
        self._fail = fail

    def analyse(self, prompt: ItemPrompt) -> ItemAnalysis:
        if self._fail:
            raise RuntimeError(f"{self.model} failed")
        return ItemAnalysis(
            item_id=prompt.item_id,
            relevance=4.0,
            actionability=4.0,
            tldr_en=self.model,
            takeaways_en=[],
            implication_en="",
            topics=["Agent"],
        )


def _prompt() -> ItemPrompt:
    return ItemPrompt("item:1", "title", "author", "paper", None, "lens")


def test_model_fallback_tries_next_model() -> None:
    attempts: list[str] = []

    def build(model: str):
        attempts.append(model)
        return _Analyser(model, fail=model == "first")

    analyser = ModelFallbackAnalyser(["first", "second"], build)
    out = analyser.analyse(_prompt())

    assert out.tldr_en == "second"
    assert attempts == ["first", "second"]


def test_model_fallback_fails_after_all_models() -> None:
    analyser = ModelFallbackAnalyser(
        ["first", "second"],
        lambda model: _Analyser(model, fail=True),
    )

    with pytest.raises(RuntimeError) as excinfo:
        analyser.analyse(_prompt())

    msg = str(excinfo.value)
    assert "after 2 model(s)" in msg
    assert "first failed" in msg
    assert "second failed" in msg
