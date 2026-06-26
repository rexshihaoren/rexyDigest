"""Load repo-root env files before CLI / Gemini (parity with Node `generate_gist.mjs`)."""

from __future__ import annotations

from pathlib import Path


def load_dotenv_repo(cwd: Path | None = None) -> None:
    """`.env.local` then `.env`, cwd-relative (same order as `scripts/generate_gist.mjs`).

    Uses python-dotenv default ``override=False``: existing OS env wins; second file
    does not clobber vars already set by the first.
    """
    from dotenv import load_dotenv

    root = Path.cwd() if cwd is None else Path(cwd)
    load_dotenv(root / ".env.local")
    load_dotenv(root / ".env")
