"""GeminiAnalyser — production LLM adapter.

Calls google-genai (`google.genai`) with JSON-mode prompt and parses the
response into an `ItemAnalysis`. API failures use short user-facing copy only —
never raw quota/rate-limit payloads in Markdown.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from . import DEFAULT_LENS, ItemAnalysis, ItemPrompt

logger = logging.getLogger(__name__)


def resolve_gemini_api_key(api_key: str | None = None) -> str:
    """Env or explicit key, stripped (parity with Node `GEMINI_API_KEY_TRIMMED`)."""
    raw = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    return raw.strip() if isinstance(raw, str) else ""


def user_facing_gemini_error(exc: BaseException) -> str:
    """Stable operator message for gist/publish — must not echo SDK or quota payloads."""
    low = str(exc).lower()
    code = getattr(exc, "status_code", None)
    if code == 429:
        return (
            "Gemini API rate limit or quota exceeded. Retry later or review "
            "plan/billing in Google AI Studio."
        )
    if code in (401, 403):
        return "Gemini API rejected the request (check API key / permissions)."
    if code == 408 or "timeout" in low or "timed out" in low or "deadline" in low:
        return "Gemini API request timed out. Retry later."
    head = str(exc)[:24].strip()
    if head.startswith("429") or " 429 " in low[:40]:
        return (
            "Gemini API rate limit or quota exceeded. Retry later or review "
            "plan/billing in Google AI Studio."
        )
    if (
        "resource_exhausted" in low
        or "too many requests" in low
        or "rate limit" in low
        or ("quota" in low and "exceed" in low)
    ):
        return (
            "Gemini API rate limit or quota exceeded. Retry later or review "
            "plan/billing in Google AI Studio."
        )
    if head.startswith("401") or head.startswith("403") or (
        "permission denied" in low or ("invalid" in low and "api key" in low)
    ):
        return "Gemini API rejected the request (check API key / permissions)."
    return "Gemini API request failed. Retry later or check connectivity."


_PROMPT_TEMPLATE = """You are scoring one piece of content for a weekly bilingual brief on AI agents and the simulation hypothesis.

{lens}

Item:
  type:    {item_type}
  title:   {title}
  author:  {author}
  payload (extract or full text, may be empty):
\"\"\"
{payload}
\"\"\"

Return ONLY valid JSON matching this schema:
{{
  "relevance":      <float 1.0-5.0>,
  "actionability":  <float 1.0-5.0>,
  "tldr_en":        <one sentence string, English>,
  "takeaways_en":   [<3-5 short bullet strings, English>],
  "implication_en": <one sentence on why a practitioner-philosopher should care>,
  "topics":         [<one or more of: "Agent", "Simulation">],
  "title_zh":       <Simplified Chinese translation of title>,
  "tldr_zh":        <SC translation of tldr_en>,
  "takeaways_zh":   [<SC translations of each takeaway, same length as takeaways_en>],
  "implication_zh": <SC translation of implication_en>,
  "topics_zh":      [<SC labels: 智能体 | 模拟>]
}}

Rules:
- Be honest. If the payload is empty or weak, score relevance/actionability low.
- "topics" must be a non-empty subset of ["Agent", "Simulation"].
- No markdown, no commentary, JSON only.
"""


try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - runtime hint only
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]


class GeminiAnalyser:
    model: str
    prompt_version: str = "v1.0"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ) -> None:
        if genai is None or genai_types is None:
            raise RuntimeError(
                "google-genai is not installed; run `pip install google-genai` "
                "(see requirements.txt)"
            )

        key = resolve_gemini_api_key(api_key)
        if not key:
            raise RuntimeError(
                "GeminiAnalyser needs GEMINI_API_KEY (or GOOGLE_API_KEY) in env or constructor "
                "(export or put in repo-root .env.local / .env, same as Node generate_gist)"
            )
        self._client = genai.Client(api_key=key)
        self._genai_types = genai_types
        self.model = model

    def analyse(self, prompt: ItemPrompt) -> ItemAnalysis:
        rendered = _PROMPT_TEMPLATE.format(
            lens=DEFAULT_LENS,
            item_type=prompt.item_type,
            title=prompt.title,
            author=prompt.author,
            payload=(prompt.payload or "").strip()[:8000],
        )
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=rendered,
                config=self._genai_types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            )
            text = (response.text or "").strip()
        except Exception as exc:  # pragma: no cover - network paths exercised via mocks
            logger.warning(
                "Gemini generate_content failed for %s (%s)",
                prompt.item_id,
                type(exc).__name__,
            )
            return _failure_analysis(prompt.item_id, user_facing_gemini_error(exc))

        return _parse_or_fallback(prompt.item_id, text)


def _parse_or_fallback(item_id: str, text: str) -> ItemAnalysis:
    """Best-effort JSON parse; on failure, return a low-conf analysis (no raw payload in TL;DR)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        stripped = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            logger.warning(
                "Gemini JSON parse failed for %s (length=%s)", item_id, len(text)
            )
            return _failure_analysis(
                item_id,
                "model returned text that was not valid JSON (check logs / rerun)",
            )

    return ItemAnalysis(
        item_id=item_id,
        relevance=_as_float(data.get("relevance"), default=1.0),
        actionability=_as_float(data.get("actionability"), default=1.0),
        tldr_en=str(data.get("tldr_en") or ""),
        takeaways_en=_as_str_list(data.get("takeaways_en")),
        implication_en=str(data.get("implication_en") or ""),
        topics=_as_str_list(data.get("topics")) or [],
        title_zh=_as_optional_str(data.get("title_zh")),
        tldr_zh=_as_optional_str(data.get("tldr_zh")),
        takeaways_zh=_as_str_list(data.get("takeaways_zh")) or None,
        implication_zh=_as_optional_str(data.get("implication_zh")),
        topics_zh=_as_str_list(data.get("topics_zh")) or None,
    )


def _failure_analysis(item_id: str, msg: str) -> ItemAnalysis:
    return ItemAnalysis(
        item_id=item_id,
        relevance=1.0,
        actionability=1.0,
        tldr_en=f"[generator error: {msg}]",
        takeaways_en=[],
        implication_en="",
        topics=[],
    )


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return max(1.0, min(5.0, float(v)))
    except (TypeError, ValueError):
        return default


def _as_str_list(v: Any) -> list[str]:
    if not isinstance(v, list):
        return []
    return [str(x) for x in v if x is not None]


def _as_optional_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None
