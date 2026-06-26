"""Repo-root dotenv loading (parity with Node generate_gist.mjs)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from rexy.env_bootstrap import load_dotenv_repo


def test_load_dotenv_prefers_env_local_over_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".env.local").write_text("GEMINI_API_KEY=from_local\n", encoding="utf-8")
    (tmp_path / ".env").write_text("GEMINI_API_KEY=from_env\n", encoding="utf-8")
    load_dotenv_repo(tmp_path)
    assert os.environ["GEMINI_API_KEY"] == "from_local"


def test_load_dotenv_env_fills_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("GEMINI_API_KEY=only_env\n", encoding="utf-8")
    load_dotenv_repo(tmp_path)
    assert os.environ["GEMINI_API_KEY"] == "only_env"


def test_resolve_gemini_api_key_trimmed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "  sk-test  ")
    from rexy.generate.llm.gemini import resolve_gemini_api_key

    assert resolve_gemini_api_key() == "sk-test"
    assert resolve_gemini_api_key("  explicit  ") == "explicit"
