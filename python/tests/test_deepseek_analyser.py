"""DeepSeek LLM adapter behavior."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from rexy.generate.llm import ItemPrompt
from rexy.generate.llm.deepseek import DeepSeekAnalyser


def _prompt() -> ItemPrompt:
    return ItemPrompt(
        item_id="item:1",
        title="World model eval",
        author="a",
        item_type="paper",
        payload="payload",
        lens="lens",
    )


def _analysis_json() -> str:
    return json.dumps({
        "relevance": 4.5,
        "actionability": 4.0,
        "tldr_en": "A useful summary.",
        "takeaways_en": ["A", "B", "C"],
        "implication_en": "Use it.",
        "topics": ["Agent", "Simulation"],
        "title_zh": "标题",
        "tldr_zh": "摘要",
        "takeaways_zh": ["甲", "乙", "丙"],
        "implication_zh": "使用它。",
        "topics_zh": ["智能体", "模拟"],
    })


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps({
            "choices": [
                {"message": {"content": _analysis_json()}}
            ]
        }).encode("utf-8")


def test_deepseek_sends_json_mode_and_disabled_thinking(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["body"] = json.loads(req.data.decode("utf-8"))
        seen["auth"] = req.headers["Authorization"]
        return _Response()

    import rexy.generate.llm.deepseek as deepseek_mod

    monkeypatch.setattr(deepseek_mod.urllib.request, "urlopen", fake_urlopen)

    analyser = DeepSeekAnalyser(
        model="deepseek-v4-pro",
        api_key="test-key",
        base_url="https://api.deepseek.com",
        thinking="disabled",
    )
    out = analyser.analyse(_prompt())

    assert out.item_id == "item:1"
    assert out.relevance == 4.5
    assert seen["url"] == "https://api.deepseek.com/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert seen["body"]["model"] == "deepseek-v4-pro"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert seen["body"]["thinking"] == {"type": "disabled"}
    assert seen["body"]["messages"][0]["role"] == "user"


def test_deepseek_api_failure_raises_without_raw_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    import rexy.generate.llm.deepseek as deepseek_mod

    def boom(*_args, **_kwargs):
        raise RuntimeError("401 invalid api key secret raw body")

    monkeypatch.setattr(deepseek_mod.urllib.request, "urlopen", boom)

    analyser = DeepSeekAnalyser(api_key="test-key")
    with pytest.raises(RuntimeError) as excinfo:
        analyser.analyse(_prompt())

    msg = str(excinfo.value)
    assert "DeepSeek analysis failed for item:1:" in msg
    assert "invalid api key" not in msg.lower()
    assert "secret raw body" not in msg.lower()


def test_deepseek_invalid_model_json_raises_without_echo(monkeypatch: pytest.MonkeyPatch) -> None:
    class BadResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "not json {{{"}}]}).encode("utf-8")

    import rexy.generate.llm.deepseek as deepseek_mod

    monkeypatch.setattr(deepseek_mod.urllib.request, "urlopen", MagicMock(return_value=BadResponse()))

    analyser = DeepSeekAnalyser(api_key="test-key")
    with pytest.raises(RuntimeError) as excinfo:
        analyser.analyse(_prompt())

    msg = str(excinfo.value)
    assert "{{{" not in msg
    assert "DeepSeek analysis failed for item:1:" in msg
    assert "json" in msg.lower()
