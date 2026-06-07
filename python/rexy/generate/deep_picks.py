"""Load generated deep-note picks from `config/deep_picks/<end>.toml`."""

from __future__ import annotations

import tomllib
from pathlib import Path

from ..domain import Window

_MAX_PICKS = 2


def picks_path(picks_root: Path, window: Window) -> Path:
    return picks_root / f"{window.end.isoformat()}.toml"


def load_deep_picks(path: Path) -> list[str]:
    """Return ordered item_ids (0..2). Raises ValueError on bad shape or >2 ids."""
    if not path.exists():
        raise FileNotFoundError(f"deep picks file missing: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    raw = data.get("item_ids")
    if raw is None:
        raise ValueError(f"{path}: missing required key 'item_ids' (use item_ids = []) for zero picks")
    if not isinstance(raw, list):
        raise ValueError(f"{path}: item_ids must be a list of strings, got {type(raw).__name__}")
    ids: list[str] = []
    for i, x in enumerate(raw):
        if not isinstance(x, str) or not x.strip():
            raise ValueError(f"{path}: item_ids[{i}] must be a non-empty string")
        ids.append(x.strip())
    if len(ids) > _MAX_PICKS:
        raise ValueError(f"{path}: at most {_MAX_PICKS} item_ids allowed, got {len(ids)}")
    return ids
