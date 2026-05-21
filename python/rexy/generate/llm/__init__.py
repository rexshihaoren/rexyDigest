"""LLM port + adapters.

The generator's per-Item summarise stage talks to LLMs through the
`LLMAnalyser` Protocol. Adapters ship behind `llm.factory.make_analyser`:

  - `InMemoryAnalyser` (`memory.py`) — deterministic, used by tests; takes
    a fixture map keyed by item_id.
  - `GeminiAnalyser`  (`gemini.py`)  — production, calls `google-genai` (`google.genai`).
  - `DeepSeekAnalyser` (`deepseek.py`) — production, calls DeepSeek's OpenAI-compatible chat API.
  - `GeminiDeepNoteWriter` / `MemoryDeepNoteWriter` (`llm/deep_note.py`) — optional second-pass Markdown per Item (`rexy deep-notes`).

Per ADR-0007, translation is part of analysis, not a separate post-step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(slots=True, frozen=True)
class ItemPrompt:
    item_id: str
    title: str
    author: str
    item_type: str
    payload: str | None
    lens: str


@dataclass(slots=True)
class ItemAnalysis:
    """One LLM round-trip per Item produces this."""

    item_id: str
    relevance: float            # 1.0 - 5.0
    actionability: float        # 1.0 - 5.0
    tldr_en: str
    takeaways_en: list[str]
    implication_en: str
    topics: list[str]           # e.g. ["Agent"], ["Simulation"], or both
    title_zh: str | None = None
    tldr_zh: str | None = None
    takeaways_zh: list[str] | None = None
    implication_zh: str | None = None
    topics_zh: list[str] | None = None


@runtime_checkable
class LLMAnalyser(Protocol):
    model: str
    prompt_version: str

    def analyse(self, prompt: ItemPrompt) -> ItemAnalysis: ...


DEFAULT_LENS = (
    "Relevance lens: 'Reality is computable simulation; AI + markets are "
    "the reality-code manipulators of our era.' Score Items by how directly "
    "they advance our understanding of either: "
    "(a) building, debugging, or steering autonomous agents and tool-using "
    "LLMs; or (b) the simulation hypothesis and the computability of reality. "
    "A high relevance score means the Item changes how a serious "
    "practitioner-philosopher in this space thinks or acts this week."
)
