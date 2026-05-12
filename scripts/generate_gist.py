#!/usr/bin/env python3
"""Generate weekly gist markdown via Gemini (Python port of generate_gist.mjs)."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "python"))


def main() -> None:
    root = Path.cwd()
    load_dotenv(root / ".env.local", override=True)
    load_dotenv(root / ".env")

    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        print("GEMINI_API_KEY required", file=sys.stderr)
        sys.exit(1)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("google-genai required: pip install google-genai", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    prompt_path = root / "prompt_weekly_gist.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    now = datetime.now()
    start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    end = now.strftime("%Y-%m-%d")
    folder = root / "Weekly_Gist"
    file_name = f"Weekly_Gist_{end}.md"
    augmented = (
        f"{prompt}\n\nEXECUTION CONTEXT\n"
        f"- Coverage window: {start} to {end}\n"
        f"- Generated at: {end}\n"
        "- If no items in window, apply fallbacks per prompt and use VERIFY_NEEDED where appropriate."
    )

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=augmented,
            config=types.GenerateContentConfig(temperature=0.4),
        )
        md = (res.text or "").strip()
    except Exception as e:  # noqa: BLE001 — surface generic failure text only
        from rexy.generate.llm.gemini import user_facing_gemini_error

        print(f"[generate_gist] {user_facing_gemini_error(e)}", file=sys.stderr)
        sys.exit(1)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / file_name
    out.write_text(f"# Weekly Gist – {now.strftime('%Y-%m-%d')}\n\n{md}\n", encoding="utf-8")
    print("✅ Created:", file_name)


if __name__ == "__main__":
    main()
