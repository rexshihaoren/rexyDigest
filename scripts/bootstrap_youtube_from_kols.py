#!/usr/bin/env python3
"""Write `config/sources/youtube.toml` from `kol_priors` ∩ `YOUTUBE_SEED`.

Usage (repo root):

  PYTHONPATH=python ./.venv/bin/python scripts/bootstrap_youtube_from_kols.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "python") not in sys.path:
    sys.path.insert(0, str(_REPO / "python"))

from rexy.generate.config import GeneratorConfig  # noqa: E402
from rexy.sources.youtube_bootstrap import (  # noqa: E402
    YOUTUBE_SEED,
    missing_seed_slugs,
    render_youtube_toml,
)

_OUT = _REPO / "config" / "sources" / "youtube.toml"


def main() -> int:
    cfg = GeneratorConfig.load(_REPO / "config" / "generator.toml")
    missing = missing_seed_slugs(cfg)
    body = render_youtube_toml(cfg)
    _OUT.write_text(body, encoding="utf-8")
    n_blocks = body.count("[[channels]]")
    print(f"Wrote {_OUT} ({n_blocks} channels, {len(YOUTUBE_SEED)} seed entries)")
    if missing:
        print("KOL priors with NO YouTube seed row (add to YOUTUBE_SEED or ignore):")
        for m in missing:
            print(f"  - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
