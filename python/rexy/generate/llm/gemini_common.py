"""Gemini API key + user-facing error strings (no google SDK import)."""

from __future__ import annotations

import os


def resolve_gemini_api_key(api_key: str | None = None) -> str:
    """Env or explicit key, stripped (parity with Node `GEMINI_API_KEY_TRIMMED`)."""
    raw = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    return raw.strip() if isinstance(raw, str) else ""


def user_facing_gemini_error(exc: BaseException) -> str:
    """Stable operator message — must not echo SDK or quota payloads."""
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
