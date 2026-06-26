"""GeminiAnalyser — production LLM adapter.

Calls google-genai (`google.genai`) with JSON-mode prompt and parses the
response into an `ItemAnalysis`. API failures raise short user-facing errors
only, so generation fails before writing fallback text into digests.
"""

from __future__ import annotations

import logging

from . import ItemAnalysis, ItemPrompt
from .gemini_common import resolve_gemini_api_key, user_facing_gemini_error
from .item_analysis import parse_item_analysis_json, render_item_analysis_prompt

logger = logging.getLogger(__name__)


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
        rendered = render_item_analysis_prompt(prompt)
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
            raise RuntimeError(
                f"Gemini analysis failed for {prompt.item_id}: {user_facing_gemini_error(exc)}"
            ) from exc

        return parse_item_analysis_json(prompt.item_id, text, "Gemini")
