"""Provider-neutral LLM factory."""

from __future__ import annotations

from rexy.generate.config import GeneratorConfig
from rexy.generate.llm import ItemAnalysis, ItemPrompt
from rexy.generate.llm.fallback import ModelFallbackAnalyser
from rexy.generate.llm.factory import make_analyser
from rexy.generate.llm.memory import InMemoryAnalyser


def _stub(prompt: ItemPrompt) -> ItemAnalysis:
    return ItemAnalysis(
        item_id=prompt.item_id,
        relevance=1.0,
        actionability=1.0,
        tldr_en="x",
        takeaways_en=[],
        implication_en="",
        topics=[],
    )


def test_factory_builds_memory_analyser() -> None:
    analyser = make_analyser("memory", GeneratorConfig(), memory_stub=_stub)
    assert isinstance(analyser, InMemoryAnalyser)


def test_generator_config_defaults_to_deepseek_provider() -> None:
    assert GeneratorConfig().llm_provider == "deepseek"


def test_factory_builds_deepseek_fallback_analyser(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.delenv("DEEPSEEK_MODEL_FALLBACKS", raising=False)
    cfg = GeneratorConfig(deepseek_model="deepseek-v4-flash")

    analyser = make_analyser("deepseek", cfg)

    assert isinstance(analyser, ModelFallbackAnalyser)
    assert analyser.model == "deepseek-v4-flash"


def test_factory_uses_deepseek_model_fallbacks_env(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_MODEL_FALLBACKS", "deepseek-v4-pro, deepseek-v4-flash")

    analyser = make_analyser("deepseek", GeneratorConfig())

    assert analyser.model == "deepseek-v4-pro,deepseek-v4-flash"
