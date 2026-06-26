#!/usr/bin/env python3
"""Write `config/sources/youtube.toml` from `kol_priors` ∩ `YOUTUBE_SEED`.

Usage (repo root):

  PYTHONPATH=python ./.venv/bin/python scripts/bootstrap_youtube_from_kols.py

By default this fail-closes through an LLM judge that verifies each configured
channel feed matches the intended KOL before writing youtube.toml.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib import request

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "python") not in sys.path:
    sys.path.insert(0, str(_REPO / "python"))

from rexy.env_bootstrap import load_dotenv_repo  # noqa: E402
from rexy.generate.config import GeneratorConfig  # noqa: E402
from rexy.sources.youtube_bootstrap import (  # noqa: E402
    YOUTUBE_SEED,
    missing_seed_slugs,
    render_youtube_toml,
)
from rexy.sources.youtube_adapter import _channel_feed_url  # noqa: E402
from rexy.sources.rss_adapter import parse_feed_document  # noqa: E402

_OUT = _REPO / "config" / "sources" / "youtube.toml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-llm-verify",
        action="store_true",
        help="write youtube.toml without judge LLM verification",
    )
    args = parser.parse_args(argv)

    load_dotenv_repo(_REPO)
    cfg = GeneratorConfig.load(_REPO / "config" / "generator.toml")
    missing = missing_seed_slugs(cfg)
    if not args.no_llm_verify:
        failures = verify_seed_channels_with_judge(cfg)
        if failures:
            print("YouTube seed verification failed; youtube.toml was not written:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1

    body = render_youtube_toml(cfg)
    _OUT.write_text(body, encoding="utf-8")
    n_blocks = body.count("[[channels]]")
    print(f"Wrote {_OUT} ({n_blocks} channels, {len(YOUTUBE_SEED)} seed entries)")
    if missing:
        print("KOL priors with NO YouTube seed row (add to YOUTUBE_SEED or ignore):")
        for m in missing:
            print(f"  - {m}")
    return 0


def verify_seed_channels_with_judge(cfg: GeneratorConfig) -> list[str]:
    failures: list[str] = []
    priors = cfg.kol_priors
    for slug in priors:
        if slug not in YOUTUBE_SEED:
            continue
        channel_id, expected_author = YOUTUBE_SEED[slug]
        snapshot = _feed_snapshot(slug, channel_id, expected_author)
        verdict = _judge_channel(snapshot, cfg)
        if not verdict.get("match"):
            reason = str(verdict.get("reason") or "judge returned mismatch")
            confidence = verdict.get("confidence", "?")
            failures.append(f"{slug}: channel_id={channel_id} confidence={confidence} reason={reason}")
    return failures


def _feed_snapshot(slug: str, channel_id: str, expected_author: str) -> dict[str, Any]:
    url = _channel_feed_url({"channel_id": channel_id})
    parsed = parse_feed_document(url)
    if getattr(parsed, "bozo", False) and not parsed.entries:
        raise RuntimeError(
            f"youtube seed {slug!r}: failed to parse channel feed {url!r}: "
            f"{getattr(parsed, 'bozo_exception', None)!r}"
        )
    feed = getattr(parsed, "feed", {}) or {}
    entries = list(getattr(parsed, "entries", []) or [])[:5]
    return {
        "slug": slug,
        "channel_id": channel_id,
        "expected_author": expected_author,
        "feed_url": url,
        "feed_title": _get(feed, "title"),
        "feed_author": _get(feed, "author") or _get(feed, "name"),
        "recent_titles": [_get(e, "title") for e in entries if _get(e, "title")],
        "recent_authors": sorted({_get(e, "author") for e in entries if _get(e, "author")}),
    }


def _judge_channel(snapshot: dict[str, Any], cfg: GeneratorConfig) -> dict[str, Any]:
    if cfg.llm_provider != "deepseek":
        raise RuntimeError("YouTube judge currently requires llm_provider = \"deepseek\"")
    key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("YouTube judge needs DEEPSEEK_API_KEY in .env.local")

    prompt = _judge_prompt(snapshot)
    body = {
        "model": cfg.deepseek_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    if cfg.deepseek_thinking:
        body["thinking"] = {"type": cfg.deepseek_thinking}

    req = request.Request(
        f"{cfg.deepseek_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    return parse_judge_response(str(content))


def _judge_prompt(snapshot: dict[str, Any]) -> str:
    return (
        "You verify whether a YouTube channel feed matches an intended KOL.\n"
        "Return ONLY JSON: {\"match\": boolean, \"confidence\": 0.0-1.0, \"reason\": string}.\n"
        "Fail closed: if feed title/authors/recent titles indicate a different person, brand, or show, match=false.\n\n"
        f"Snapshot:\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}"
    )


def parse_judge_response(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data.get("match"), bool):
        raise RuntimeError("judge response missing boolean `match`")
    return data


def _get(obj: Any, key: str) -> str:
    if hasattr(obj, "get"):
        value = obj.get(key)
    else:
        value = getattr(obj, key, "")
    return str(value or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
