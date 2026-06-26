"""Gemini failures must not leak raw API / quota payloads into published Markdown."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rexy.generate.llm import ItemPrompt
from rexy.generate.llm.gemini import GeminiAnalyser, user_facing_gemini_error


def test_user_facing_maps_quota_blob_without_echo() -> None:
    blob = (
        "429 You exceeded your current quota, please check your plan and billing details. "
        "Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, "
        "limit: 20, model: gemini-2.5-flash Please retry in 55s. [violations { quota_metric: \"x\" }]"
    )
    out = user_facing_gemini_error(Exception(blob))
    assert "429" not in out
    assert "violations" not in out.lower()
    assert "generativelanguage.googleapis.com" not in out
    assert "quota_metric" not in out
    assert "retry in" not in out.lower()
    assert len(out) < 200


def test_user_facing_maps_auth_style_errors() -> None:
    out = user_facing_gemini_error(Exception("401 invalid api key"))
    assert "invalid api key" not in out.lower()
    assert "401" not in out


def test_user_facing_generic_when_unclassified() -> None:
    out = user_facing_gemini_error(RuntimeError("something weird happened"))
    assert "weird" not in out.lower()
    assert len(out) < 120


def test_gemini_analyse_exception_fails_without_raw_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: Gemini failure must abort generation without raw SDK / HTTP bodies."""

    import rexy.generate.llm.gemini as gemini_mod

    if gemini_mod.genai is None:
        pytest.skip("google-genai not installed")

    def boom(*_a, **_k):
        raise Exception(
            "429 You exceeded quota generativelanguage.googleapis.com/generate_content_free_tier_requests"
        )

    mock_client = MagicMock()
    mock_client.models.generate_content = boom
    mock_pkg = MagicMock()
    mock_pkg.Client = lambda **_k: mock_client
    monkeypatch.setattr(gemini_mod, "genai", mock_pkg)

    a = GeminiAnalyser(model="gemini-2.5-flash", api_key="test-key")
    p = ItemPrompt(
        item_id="x",
        title="t",
        author="a",
        item_type="blog",
        payload="p",
        lens="l",
    )
    with pytest.raises(RuntimeError) as excinfo:
        a.analyse(p)
    msg = str(excinfo.value)
    assert "generativelanguage" not in msg
    assert "429" not in msg
    assert "Gemini analysis failed for x:" in msg


def test_parse_failure_fails_without_raw_response(monkeypatch: pytest.MonkeyPatch) -> None:
    import rexy.generate.llm.gemini as gemini_mod

    if gemini_mod.genai is None:
        pytest.skip("google-genai not installed")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "not json {{{"
    mock_client.models.generate_content = MagicMock(return_value=mock_response)
    mock_pkg = MagicMock()
    mock_pkg.Client = lambda **_k: mock_client
    monkeypatch.setattr(gemini_mod, "genai", mock_pkg)

    a = GeminiAnalyser(model="gemini-2.5-flash", api_key="test-key")
    p = ItemPrompt(
        item_id="y",
        title="t",
        author="a",
        item_type="paper",
        payload=None,
        lens="l",
    )
    with pytest.raises(RuntimeError) as excinfo:
        a.analyse(p)
    msg = str(excinfo.value)
    assert "{{{" not in msg
    assert "Gemini analysis failed for y:" in msg
    assert "json" in msg.lower()
