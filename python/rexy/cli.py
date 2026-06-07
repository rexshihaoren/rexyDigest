"""Command-line entry: `python -m rexy.cli ...`

Subcommands
-----------
- `ingest`  Run all configured Source Adapters over a Window and update the corpus.
- `status`  Print a short summary of the corpus.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from .corpus.items_store import ItemsStore
from .corpus.runs_store import RunsStore
from .domain import Window
from .env_bootstrap import load_dotenv_repo
from .generate.config import GeneratorConfig
from .generate.pipeline import run_generation
from .ingest import run_ingestion
from .publish.cli import cmd_publish
from .sources._registry import load_adapters


DEFAULT_CORPUS = Path("corpus")
DEFAULT_CONFIG = Path("config/sources")
DEFAULT_GENERATOR_CONFIG = Path("config/generator.toml")
DEFAULT_GIST_DIR = Path("Weekly_Gist")
DEFAULT_PUBLIC_DIR = Path("Weekly_Gist/Public")
DEFAULT_DEEP_PICKS_DIR = Path("config/deep_picks")
DEFAULT_KC_INBOX = Path("KnowledgeCard_Inbox")


def main(argv: list[str] | None = None) -> int:
    load_dotenv_repo()
    parser = argparse.ArgumentParser(prog="rexy", description="Rexy Digest pipeline")
    parser.add_argument(
        "--corpus", type=Path, default=DEFAULT_CORPUS,
        help=f"corpus root (default: {DEFAULT_CORPUS})",
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG,
        help=f"adapter config dir (default: {DEFAULT_CONFIG})",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    ingest = sub.add_parser("ingest", help="Run ingestion over a Window")
    ingest.add_argument(
        "--window", type=str, default=None,
        help="Window in form YYYY-MM-DD/YYYY-MM-DD (default: last 7 days)",
    )
    ingest.add_argument(
        "--end", type=str, default=None,
        help="Window end YYYY-MM-DD; start = end-7d. Overrides --window if both given.",
    )

    sub.add_parser("status", help="Print corpus summary")

    gen = sub.add_parser(
        "generate",
        help="Run Phase-2 generator: corpus -> Selection + Markdown gist",
    )
    gen.add_argument(
        "--window", type=str, default=None,
        help="Window to generate for (default: latest ingestion run's window)",
    )
    gen.add_argument(
        "--end", type=str, default=None,
        help="Window end YYYY-MM-DD; start = end-7d (overrides --window).",
    )
    gen.add_argument(
        "--gist-dir", type=Path, default=DEFAULT_GIST_DIR,
        help=f"where to write Weekly_Gist_<end>.md (default: {DEFAULT_GIST_DIR})",
    )
    gen.add_argument(
        "--generator-config", type=Path, default=DEFAULT_GENERATOR_CONFIG,
        help=f"generator config TOML (default: {DEFAULT_GENERATOR_CONFIG})",
    )
    gen.add_argument(
        "--llm", choices=["gemini", "deepseek", "memory"], default=None,
        help="LLM provider override (default: generator config; memory = deterministic fixture)",
    )

    pub = sub.add_parser(
        "publish",
        help="Render a Selection JSONL into a bilingual public Markdown brief (LLM-free).",
    )
    pub.add_argument(
        "--window", type=str, default=None,
        help="Window to publish (default: latest ingestion run's window)",
    )
    pub.add_argument(
        "--end", type=str, default=None,
        help="Window end YYYY-MM-DD (overrides --window)",
    )
    pub.add_argument(
        "--public-dir", type=Path, default=DEFAULT_PUBLIC_DIR,
        help=f"where to write Weekly_Brief_Public_<end>.md (default: {DEFAULT_PUBLIC_DIR})",
    )

    par = sub.add_parser(
        "parity",
        help="Compare a Node-published brief and a Python-published brief for structural parity.",
    )
    par.add_argument("--node", type=Path, required=True, help="Node-published brief markdown")
    par.add_argument("--python", type=Path, required=True, help="Python-published brief markdown")

    deep = sub.add_parser(
        "deep-notes",
        help="Interactive second-pass Gemini deep-note picker.",
    )
    deep_sub = deep.add_subparsers(dest="deep_cmd", required=True)
    deep_pick = deep_sub.add_parser(
        "pick",
        help="Review public overview AI×Simulation candidates, pick up to 2, and generate deep notes.",
    )
    deep_pick.add_argument(
        "--end", type=str, default=None,
        help="Window end YYYY-MM-DD; omit to choose from latest Selection dates.",
    )
    deep_pick.add_argument(
        "--deep-picks-dir", type=Path, default=DEFAULT_DEEP_PICKS_DIR,
        help=f"where to write generated pick audit TOML (default: {DEFAULT_DEEP_PICKS_DIR})",
    )
    deep_pick.add_argument(
        "--inbox-dir", type=Path, default=DEFAULT_KC_INBOX,
        help=f"where to write deep_*.md (default: {DEFAULT_KC_INBOX})",
    )
    deep_pick.add_argument(
        "--public-dir", type=Path, default=DEFAULT_PUBLIC_DIR,
        help=f"where to require Weekly_Brief_Public_<end>.md (default: {DEFAULT_PUBLIC_DIR})",
    )
    deep_pick.add_argument(
        "--generator-config", type=Path, default=DEFAULT_GENERATOR_CONFIG,
        help=f"generator config TOML (default: {DEFAULT_GENERATOR_CONFIG})",
    )

    args = parser.parse_args(argv)

    if args.cmd == "ingest":
        return _cmd_ingest(args)
    if args.cmd == "status":
        return _cmd_status(args)
    if args.cmd == "generate":
        return _cmd_generate(args)
    if args.cmd == "publish":
        return cmd_publish(args)
    if args.cmd == "parity":
        return _cmd_parity(args)
    if args.cmd == "deep-notes":
        if args.deep_cmd == "pick":
            return _cmd_deep_notes_pick(args)
        parser.error(f"unknown deep-notes command {args.deep_cmd}")
    parser.error(f"unknown command {args.cmd}")
    return 2


def _cmd_parity(args: argparse.Namespace) -> int:
    from .publish.parity import compare
    node_md = args.node.read_text(encoding="utf-8")
    py_md = args.python.read_text(encoding="utf-8")
    result = compare(node_md, py_md)
    if result.ok:
        print(f"[rexy] PARITY OK: {args.node.name} ~ {args.python.name}")
        return 0
    print(f"[rexy] PARITY FAILED: {len(result.differences)} difference(s)")
    for d in result.differences:
        print(f"  - {d}")
    return 1


def _resolve_window(args: argparse.Namespace) -> Window:
    end_str = args.end or os.environ.get("END_DATE") or os.environ.get("TARGET_DATE")
    if end_str:
        end = date.fromisoformat(end_str)
        return Window(start=end - timedelta(days=7), end=end)
    if args.window:
        return Window.parse(args.window)
    today = date.today()
    return Window(start=today - timedelta(days=7), end=today)


def _cmd_ingest(args: argparse.Namespace) -> int:
    window = _resolve_window(args)
    config_dir: Path = args.config
    corpus_root: Path = args.corpus

    print(f"[rexy] ingest window={window} corpus={corpus_root} config={config_dir}")
    adapters = load_adapters(config_dir)
    if not adapters:
        print(f"[rexy] no adapters configured under {config_dir}", file=sys.stderr)
        return 1
    print(f"[rexy] adapters: {', '.join(a.name for a in adapters)}")

    run = run_ingestion(adapters, window, corpus_root)
    total_yielded = sum(a.items_yielded for a in run.adapters)
    total_new = sum(a.items_new for a in run.adapters)
    total_updated = sum(a.items_updated for a in run.adapters)
    error_count = sum(len(a.errors) for a in run.adapters)
    duration = (run.finished_at - run.started_at).total_seconds() if run.finished_at else 0.0

    print(f"[rexy] run_id={run.run_id} duration={duration:.2f}s")
    for stat in run.adapters:
        print(
            f"  {stat.name:24s} yielded={stat.items_yielded:4d} "
            f"new={stat.items_new:4d} updated={stat.items_updated:4d} "
            f"errors={len(stat.errors)} ({stat.duration_s:.2f}s)"
        )
        for err in stat.errors:
            print(f"    ! {err}")
    print(
        f"[rexy] total: yielded={total_yielded} new={total_new} "
        f"updated={total_updated} errors={error_count}"
    )
    return 1 if error_count and total_yielded == 0 else 0


def _resolve_generation_window(args: argparse.Namespace, corpus_root: Path) -> Window:
    end_str = args.end or os.environ.get("END_DATE") or os.environ.get("TARGET_DATE")
    if end_str:
        end = date.fromisoformat(end_str)
        return Window(start=end - timedelta(days=7), end=end)
    if args.window:
        return Window.parse(args.window)
    runs = RunsStore(corpus_root / "runs")
    latest = runs.latest_window()
    if latest is None:
        raise SystemExit(
            f"[rexy] no ingestion run found under {corpus_root}/runs; "
            "pass --window or run `rexy ingest` first"
        )
    return latest


def _cmd_generate(args: argparse.Namespace) -> int:
    corpus_root: Path = args.corpus
    window = _resolve_generation_window(args, corpus_root)
    config = GeneratorConfig.load(args.generator_config)
    provider = args.llm or config.llm_provider

    print(f"[rexy] generate window={window} corpus={corpus_root}")
    print(f"[rexy] llm provider={provider} model={_provider_model(provider, config)}")

    from .generate.llm import ItemAnalysis, ItemPrompt
    from .generate.llm.factory import make_analyser

    def _stub(prompt: ItemPrompt) -> ItemAnalysis:
        return ItemAnalysis(
            item_id=prompt.item_id,
            relevance=3.0,
            actionability=3.0,
            tldr_en=f"[smoke-test stub] {prompt.title[:80]}",
            takeaways_en=["Memory adapter active.", "No real LLM call.", "Use --llm gemini/deepseek for real run."],
            implication_en="Smoke-test only; switch to --llm gemini/deepseek for real analysis.",
            topics=["Agent"],
            title_zh="（占位）",
            tldr_zh="（占位 TL;DR）",
            takeaways_zh=["占位 1", "占位 2", "占位 3"],
            implication_zh="（占位）",
            topics_zh=["智能体"],
        )

    analyser = make_analyser(provider, config, memory_stub=_stub)

    run = run_generation(window, config, analyser, corpus_root, args.gist_dir)
    duration = (run.finished_at - run.started_at).total_seconds() if run.finished_at else 0.0

    print(f"[rexy] run_id={run.run_id} duration={duration:.2f}s")
    print(f"  items_in_corpus={run.items_in_corpus}")
    print(f"  after prefilter={run.items_after_prefilter}")
    print(f"  after prerank  ={run.items_after_prerank}")
    print(f"  in selection   ={run.items_in_selection}")
    print(f"  selection      ={run.selection_path}")
    print(f"  gist           ={run.gist_path}")
    return 0 if run.items_in_selection > 0 else 1


def _provider_model(provider: str, config: GeneratorConfig) -> str:
    provider = provider.strip().lower()
    if provider == "gemini":
        return config.gemini_model
    if provider == "deepseek":
        return config.deepseek_model
    if provider == "memory":
        return "memory-stub"
    return "(unknown)"


def _cmd_deep_notes_pick(args: argparse.Namespace) -> int:
    from .generate.deep_note_picker import (
        available_selection_ends,
        run_interactive_deep_note_pick,
        window_for_end,
    )
    from .generate.deep_notes import make_deep_note_writer

    if not sys.stdin.isatty():
        print("[rexy] deep-notes pick requires an interactive terminal", file=sys.stderr)
        return 1

    corpus_root: Path = args.corpus
    try:
        if args.end:
            window = window_for_end(date.fromisoformat(args.end))
        else:
            ends = available_selection_ends(corpus_root, limit=10)
            if not ends:
                print(f"[rexy] no Selection files found under {corpus_root / 'selections'}", file=sys.stderr)
                return 1
            window = window_for_end(_choose_selection_end(ends))

        cfg = GeneratorConfig.load(args.generator_config)

        def writer_factory():
            return make_deep_note_writer("gemini", cfg.gemini_model)

        run = run_interactive_deep_note_pick(
            window=window,
            corpus_root=corpus_root,
            public_dir=args.public_dir,
            picks_root=args.deep_picks_dir,
            inbox_dir=args.inbox_dir,
            config=cfg,
            writer_factory=writer_factory,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"[rexy] {e}", file=sys.stderr)
        return 1

    if run.item_ids:
        print(f"[rexy] picks_file={run.picks_file}")
    for path in run.written:
        print(f"[rexy] wrote {path}")
    for path in run.skipped_existing:
        print(f"[rexy] skipped existing {path}")
    return 0


def _choose_selection_end(ends: list[date]) -> date:
    latest = ends[0]
    if _ask_cli_yes_no(f"Use latest available selection: {latest.isoformat()}? [y/n]: "):
        return latest

    print("Available selection windows:")
    for index, end in enumerate(ends, start=1):
        print(f"{index}. {end.isoformat()}")
    while True:
        raw = input(f"Choose end date [1-{len(ends)}]: ").strip()
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a number.")
            continue
        if 1 <= value <= len(ends):
            return ends[value - 1]
        print(f"Please enter a number from 1 to {len(ends)}.")


def _ask_cli_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False
        print("Please answer y or n.")


def _cmd_status(args: argparse.Namespace) -> int:
    corpus_root: Path = args.corpus
    items = ItemsStore(corpus_root / "items.jsonl").read_all()
    by_type: dict[str, int] = {}
    for it in items:
        by_type[it.source_type.value] = by_type.get(it.source_type.value, 0) + 1
    latest = RunsStore(corpus_root / "runs").latest_window()

    print(f"[rexy] corpus={corpus_root}")
    print(f"  items: {len(items)}")
    for st, n in sorted(by_type.items()):
        print(f"    {st:10s} {n}")
    print(f"  latest ingestion window: {latest if latest else '(none)'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
