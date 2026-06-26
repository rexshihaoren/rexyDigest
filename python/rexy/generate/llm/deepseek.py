"""DeepSeekAnalyser — OpenAI-compatible production LLM adapter."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from . import ItemAnalysis, ItemPrompt
from .item_analysis import parse_item_analysis_json, render_item_analysis_prompt

logger = logging.getLogger(__name__)


def resolve_deepseek_api_key(api_key: str | None = None) -> str:
    raw = api_key or os.environ.get("DEEPSEEK_API_KEY") or ""
    return raw.strip() if isinstance(raw, str) else ""


def user_facing_deepseek_error(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 429:
            return "DeepSeek API rate limit or quota exceeded. Retry later or review account billing."
        if exc.code in (401, 403):
            return "DeepSeek API rejected the request (check API key / permissions)."
        if exc.code == 408:
            return "DeepSeek API request timed out. Retry later."
    low = str(exc).lower()
    if "timeout" in low or "timed out" in low:
        return "DeepSeek API request timed out. Retry later."
    if "rate limit" in low or "too many requests" in low or ("quota" in low and "exceed" in low):
        return "DeepSeek API rate limit or quota exceeded. Retry later or review account billing."
    if "unauthorized" in low or "forbidden" in low or ("invalid" in low and "key" in low):
        return "DeepSeek API rejected the request (check API key / permissions)."
    return "DeepSeek API request failed. Retry later or check connectivity."


class DeepSeekAnalyser:
    model: str
    prompt_version: str = "v1.0"

    def __init__(
        self,
        model: str = "deepseek-v4-pro",
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com",
        thinking: str = "disabled",
        timeout_s: float = 60.0,
    ) -> None:
        key = resolve_deepseek_api_key(api_key)
        if not key:
            raise RuntimeError(
                "DeepSeekAnalyser needs DEEPSEEK_API_KEY in env or constructor "
                "(export or put in repo-root .env.local / .env)"
            )
        self._api_key = key
        self._base_url = base_url.rstrip("/")
        self._thinking = thinking
        self._timeout_s = timeout_s
        self.model = model

    def analyse(self, prompt: ItemPrompt) -> ItemAnalysis:
        rendered = render_item_analysis_prompt(prompt)
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": rendered}],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }
        if self._thinking:
            body["thinking"] = {"type": self._thinking}

        try:
            req = urllib.request.Request(
                f"{self._base_url}/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout_s) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = _extract_message_content(data)
        except Exception as exc:  # pragma: no cover - network paths exercised via mocks
            logger.warning(
                "DeepSeek chat completion failed for %s (%s)",
                prompt.item_id,
                type(exc).__name__,
            )
            raise RuntimeError(
                f"DeepSeek analysis failed for {prompt.item_id}: {user_facing_deepseek_error(exc)}"
            ) from exc

        return parse_item_analysis_json(prompt.item_id, text, "DeepSeek")


def _extract_message_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("DeepSeek response did not include message content") from exc
    return str(content or "").strip()
