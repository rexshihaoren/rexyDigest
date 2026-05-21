"""CLI bootstrap safety helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _script_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "bootstrap_youtube_from_kols.py"
    spec = importlib.util.spec_from_file_location("bootstrap_youtube_from_kols", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_judge_prompt_fail_closes_on_mismatch() -> None:
    script = _script_module()
    prompt = script._judge_prompt({
        "slug": "karpathy",
        "channel_id": "UCoookXUzPciGrEZEXmh4Jjg",
        "expected_author": "Andrej Karpathy",
        "feed_title": "Sesame Street",
        "feed_author": "Sesame Street",
        "recent_titles": ["Cookie Monster sings"],
    })

    assert "Fail closed" in prompt
    assert "match=false" in prompt
    assert "Sesame Street" in prompt
    assert "Andrej Karpathy" in prompt


def test_parse_judge_response_requires_boolean_match() -> None:
    script = _script_module()

    assert script.parse_judge_response('{"match": false, "confidence": 0.99, "reason": "wrong channel"}')[
        "match"
    ] is False
    with pytest.raises(RuntimeError, match="boolean"):
        script.parse_judge_response('{"match": "false"}')
