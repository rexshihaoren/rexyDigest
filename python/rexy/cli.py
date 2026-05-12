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
        "--llm", choices=["gemini", "memory"], default="gemini",
        help="which LLM adapter to use (memory = deterministic fixture for smoke tests)",
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

    print(f"[rexy] generate window={window} corpus={corpus_root}")
    print(f"[rexy] llm adapter={args.llm} model={config.model}")

    if args.llm == "gemini":
        from .generate.llm.gemini import GeminiAnalyser
        analyser = GeminiAnalyser(model=config.model)
    else:
        from .generate.llm.memory import InMemoryAnalyser
        from .generate.llm import ItemAnalysis, ItemPrompt

        def _stub(prompt: ItemPrompt) -> ItemAnalysis:
            return ItemAnalysis(
                item_id=prompt.item_id,
                relevance=3.0,
                actionability=3.0,
                tldr_en=f"[smoke-test stub] {prompt.title[:80]}",
                takeaways_en=["Memory adapter active.", "No real LLM call.", "Use --llm gemini for real run."],
                implication_en="Smoke-test only; switch to --llm gemini for real analysis.",
                topics=["Agent"],
                title_zh="（占位）",
                tldr_zh="（占位 TL;DR）",
                takeaways_zh=["占位 1", "占位 2", "占位 3"],
                implication_zh="（占位）",
                topics_zh=["智能体"],
            )
        analyser = InMemoryAnalyser(analyse_fn=_stub, model="memory-stub", prompt_version=config.prompt_version)

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
