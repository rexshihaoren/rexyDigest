"""Generator configuration with defaults.

Loaded from `config/generator.toml` if present, falls back to defaults that
match the prompt's `prompt_weekly_gist.md` constants. Only non-default knobs
need to appear in the file.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULT_KEYWORDS_AGENT: tuple[str, ...] = (
    "agent", "agentic", "autonomous agent", "llm agent", "toolformer",
    "tool use", "tool-use", "rag", "chain-of-thought", "prompt engineering",
    "multi-agent", "agentic ai", "react agent", "world model",
)
_DEFAULT_KEYWORDS_SIM: tuple[str, ...] = (
    "simulation hypothesis", "simulation argument", "ancestor simulation",
    "are we living in a simulation", "simulation evidence", "reality+",
    "simulation theory", "digital physics",
)
_DEFAULT_KEYWORDS_AI_SIM_BRIDGE: tuple[str, ...] = (
    "world model", "world models", "digital physics", "simulation-based eval",
    "simulation-based evals", "simulation based eval", "simulation based evals",
    "simulation eval", "simulation evals", "simulation evaluation",
    "simulation evaluations", "synthetic world", "synthetic worlds",
    "consciousness modeling", "epistemic simulation",
)
_DEFAULT_KOL_PRIORS: dict[str, float] = {
    # Authors / outlets that get a ranking boost (case-insensitive substring).
    "karpathy": 1.5,
    "lilian weng": 1.4,
    "simon willison": 1.2,
    "latent space": 1.3,
    "hamel husain": 1.2,
    "jim fan": 1.4,
    "yannic kilcher": 1.3,
    "shane legg": 1.4,
    "harrison chase": 1.2,
    "jerry liu": 1.2,
    "tegmark": 1.3,
    "sean carroll": 1.3,
    "scott aaronson": 1.3,
    "wolfram": 1.2,
    "anil seth": 1.2,
    "nick bostrom": 1.4,
}


@dataclass(slots=True)
class GeneratorConfig:
    keywords_agent: tuple[str, ...] = _DEFAULT_KEYWORDS_AGENT
    keywords_sim: tuple[str, ...] = _DEFAULT_KEYWORDS_SIM
    keywords_ai_sim_bridge: tuple[str, ...] = _DEFAULT_KEYWORDS_AI_SIM_BRIDGE
    kol_priors: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_KOL_PRIORS))

    shortlist_size: int = 30      # top-N out of pre-rank
    final_size: int = 8           # top-N in the Selection
    min_sim_bridge_items: int = 2
    max_agent_only_items: int = 3
    novelty_lookback_weeks: int = 4  # how far back to check for similar prior items
    novelty_similarity_threshold: float = 0.6  # 0..1; above means "we covered this"

    # Composite formula weights (per ADR-0004 + prompt). Must sum to 1.0.
    weight_relevance: float = 0.4
    weight_novelty: float = 0.3
    weight_actionability: float = 0.3

    model: str = "gemini-2.5-flash"
    prompt_version: str = "v1.0"

    @classmethod
    def load(cls, path: Path | None = None) -> GeneratorConfig:
        cfg = cls()
        if path is None or not path.exists():
            return cfg
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if not hasattr(cfg, key):
                raise ValueError(
                    f"{path}: unknown generator config key {key!r}"
                )
            setattr(cfg, key, value)
        return cfg

    @property
    def all_keywords(self) -> tuple[str, ...]:
        return (
            tuple(self.keywords_agent)
            + tuple(self.keywords_sim)
            + tuple(self.keywords_ai_sim_bridge)
        )
