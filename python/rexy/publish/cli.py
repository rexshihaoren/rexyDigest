"""Publish command implementation (called from `rexy.cli`)."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..corpus.items_store import ItemsStore
from ..corpus.runs_store import RunsStore
from ..corpus.selections_store import SelectionsStore
from ..domain import Window
from .renderer import render_public_brief


def cmd_publish(args: argparse.Namespace) -> int:
    corpus_root: Path = args.corpus
    public_dir: Path = args.public_dir

    if args.window:
        window = Window.parse(args.window)
    elif args.end:
        from datetime import date, timedelta
        end = date.fromisoformat(args.end)
        window = Window(start=end - timedelta(days=7), end=end)
    else:
        latest = RunsStore(corpus_root / "runs").latest_window()
        if latest is None:
            print(f"[rexy] no ingestion run; pass --window or run `rexy ingest` first")
            return 1
        window = latest

    selections = SelectionsStore(corpus_root / "selections")
    entries = selections.read(window)
    if not entries:
        print(f"[rexy] no Selection at {selections._path_for(window)}; run `rexy generate` first")
        return 1

    items_by_id = {it.id: it for it in ItemsStore(corpus_root / "items.jsonl").read_all()}
    md = render_public_brief(window, entries, items_by_id)

    public_dir.mkdir(parents=True, exist_ok=True)
    out = public_dir / f"Weekly_Brief_Public_{window.end.isoformat()}.md"
    out.write_text(md, encoding="utf-8")
    print(f"[rexy] wrote {out} ({len(entries)} items)")
    return 0
