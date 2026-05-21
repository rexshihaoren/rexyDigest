"""LLM analyser factory.

Keep provider selection here so CLI and future callers do not depend on
vendor-specific adapter construction.
"""

from __future__ import annotations

from collections.abc import Callable
import os

from ..config import GeneratorConfig
from . import ItemAnalysis, ItemPrompt, LLMAnalyser


def make_analyser(
    provider: str,
    config: GeneratorConfig,
    memory_stub: Callable[[ItemPrompt], ItemAnalysis] | None = None,
) -> LLMAnalyser:
    provider = provider.strip().lower()
    if provider == "gemini":
        from .gemini import GeminiAnalyser
        from .fallback import ModelFallbackAnalyser

        models = _model_fallbacks("GEMINI_MODEL_FALLBACKS", config.gemini_model)
        return ModelFallbackAnalyser(models, lambda model: GeminiAnalyser(model=model))
    if provider == "deepseek":
        from .deepseek import DeepSeekAnalyser
        from .fallback import ModelFallbackAnalyser

        models = _model_fallbacks("DEEPSEEK_MODEL_FALLBACKS", config.deepseek_model)
        return ModelFallbackAnalyser(
            models,
            lambda model: DeepSeekAnalyser(
                model=model,
                base_url=config.deepseek_base_url,
                thinking=config.deepseek_thinking,
            ),
        )
    if provider == "memory":
        from .memory import InMemoryAnalyser

        if memory_stub is None:
            raise ValueError("memory provider requires `memory_stub`")
        return InMemoryAnalyser(
            analyse_fn=memory_stub,
            model="memory-stub",
            prompt_version=config.prompt_version,
        )
    raise ValueError(f"unknown LLM provider {provider!r}")


def _model_fallbacks(env_name: str, default_model: str) -> list[str]:
    raw = os.environ.get(env_name, "")
    models = [m.strip() for m in raw.split(",") if m.strip()]
    return models or [default_model]
