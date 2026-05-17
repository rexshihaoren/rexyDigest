"""Second-pass LLM: single-topic deep note as Markdown (knowledgecard-ready)."""

from __future__ import annotations

import logging
import re
from typing import Protocol, runtime_checkable

from .gemini_common import resolve_gemini_api_key, user_facing_gemini_error

logger = logging.getLogger(__name__)

_DEEP_PROMPT = """You are writing ONE standalone deep-dive note for a practitioner who tracks AI agents and the simulation hypothesis.

Write in **Markdown only** (no JSON). Audience: same as a personal research card — dense, honest, no clickbait.

Include:
- H1 title = the article title (verbatim or lightly cleaned).
- One short front-matter block as a bullet list: **Source URL**, **Author**, **Published** (ISO date if known), **Item id** (verbatim).
- Sections: Summary, Why it matters, Claims & evidence (what is asserted vs supported), Open questions / limits, Optional: one paragraph 中文要点 (Simplified Chinese).

Rules:
- Ground every factual claim in the payload below; if payload thin, say so explicitly.
- Do not invent URLs, quotes, or paper IDs.
- Length: roughly 600–1500 English words unless payload is tiny (then shorter).

Item id: {item_id}
Type: {item_type}
Title: {title}
Author: {author}
URL: {url}

Payload:
\"\"\"
{payload}
\"\"\"
"""


@runtime_checkable
class DeepNoteWriter(Protocol):
    model: str

    def write(self, *, item_id: str, item_type: str, title: str, author: str, url: str, payload: str) -> str:
        """Return Markdown body (full note)."""


class GeminiDeepNoteWriter:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None) -> None:
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("google-genai not installed") from exc

        key = resolve_gemini_api_key(api_key)
        if not key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY required for deep notes")
        self._client = genai.Client(api_key=key)
        self._types = genai_types
        self.model = model

    def write(
        self,
        *,
        item_id: str,
        item_type: str,
        title: str,
        author: str,
        url: str,
        payload: str,
    ) -> str:
        text = (payload or "").strip()[:24000]
        rendered = _DEEP_PROMPT.format(
            item_id=item_id,
            item_type=item_type,
            title=title,
            author=author,
            url=url,
            payload=text or "(empty)",
        )
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=rendered,
                config=self._types.GenerateContentConfig(temperature=0.35),
            )
            return (response.text or "").strip()
        except Exception as exc:  # pragma: no cover
            logger.warning("Gemini deep note failed for %s (%s)", item_id, type(exc).__name__)
            err = user_facing_gemini_error(exc)
            return f"# {title}\n\n**[generator error: {err}]**\n\n_Item id:_ `{item_id}`\n"


class MemoryDeepNoteWriter:
    """Deterministic stub for tests / smoke without API."""

    model: str = "memory-deep-stub"

    def write(
        self,
        *,
        item_id: str,
        item_type: str,
        title: str,
        author: str,
        url: str,
        payload: str,
    ) -> str:
        return (
            f"# {title}\n\n"
            f"- **Source URL:** {url}\n"
            f"- **Author:** {author}\n"
            f"- **Item id:** `{item_id}`\n\n"
            "## Summary\n\n"
            f"[memory stub] Deep note for type={item_type}. Payload chars={len(payload or '')}.\n"
        )


def safe_filename_part(item_id: str, max_len: int = 80) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", item_id).strip("_")
    return s[:max_len] if len(s) > max_len else s
