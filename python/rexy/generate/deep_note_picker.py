"""Interactive deep-note picker.

This is the only user-facing deep-note workflow: review public Top 3 overview
candidates, choose at most two AI x Simulation items, write an audit TOML, then
generate notes.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from ..corpus.items_store import ItemsStore
from ..corpus.payloads_store import PayloadsStore
from ..corpus.selections_store import SelectionsStore
from ..domain import Item, SelectionEntry, Window, now_utc
from ..publish.renderer import select_overview_highlights, select_public_entries
from .config import GeneratorConfig
from .deep_note_format import prepare_deep_note_markdown
from .deep_picks import picks_path
from .llm.deep_note import DeepNoteWriter, safe_filename_part

MAX_DEEP_NOTE_PICKS = 2
PICKS_SOURCE = "public_top3_overview_ai_sim"

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]
WriterFactory = Callable[[], DeepNoteWriter]


@dataclass(slots=True)
class DeepNoteCandidate:
    entry: SelectionEntry
    item: Item
    payload_chars: int
    ai_reason: str
    sim_reason: str


@dataclass(slots=True)
class SkippedCandidate:
    entry: SelectionEntry
    item: Item
    reason: str


@dataclass(slots=True)
class DeepNotePickRun:
    window: Window
    picks_file: Path
    item_ids: list[str]
    written: list[Path]
    skipped_existing: list[Path]


def available_selection_ends(corpus_root: Path, limit: int = 10) -> list[date]:
    root = corpus_root / "selections"
    dates: list[date] = []
    for path in root.glob("Selection_*.jsonl"):
        raw = path.stem.removeprefix("Selection_")
        try:
            dates.append(date.fromisoformat(raw))
        except ValueError:
            continue
    return sorted(dates, reverse=True)[:limit]


def window_for_end(end: date) -> Window:
    return Window(start=end - timedelta(days=7), end=end)


def public_brief_path(public_dir: Path, window: Window) -> Path:
    return public_dir / f"Weekly_Brief_Public_{window.end.isoformat()}.md"


def collect_deep_note_candidates(
    window: Window,
    corpus_root: Path,
    config: GeneratorConfig,
) -> tuple[list[DeepNoteCandidate], list[SkippedCandidate]]:
    selections = SelectionsStore(corpus_root / "selections").read(window)
    items_by_id = {it.id: it for it in ItemsStore(corpus_root / "items.jsonl").read_all()}
    payloads = PayloadsStore(corpus_root / "payloads")

    public_entries = select_public_entries(selections)
    overview_pairs = select_overview_highlights(public_entries, items_by_id)

    candidates: list[DeepNoteCandidate] = []
    skipped: list[SkippedCandidate] = []
    for entry, item in overview_pairs:
        ai_reason = _signal_reason(entry, item, tuple(config.keywords_agent), "Agent")
        sim_reason = _signal_reason(
            entry,
            item,
            tuple(config.keywords_sim) + tuple(config.keywords_ai_sim_bridge),
            "Simulation",
        )
        if not ai_reason or not sim_reason:
            missing = []
            if not ai_reason:
                missing.append("AI/Agent signal")
            if not sim_reason:
                missing.append("Simulation signal")
            skipped.append(SkippedCandidate(entry=entry, item=item, reason="missing " + " and ".join(missing)))
            continue

        payload_chars = 0
        if item.payload_ref and payloads.exists(item.payload_ref):
            payload_chars = len(payloads.read(item.payload_ref))
        candidates.append(DeepNoteCandidate(
            entry=entry,
            item=item,
            payload_chars=payload_chars,
            ai_reason=ai_reason,
            sim_reason=sim_reason,
        ))
    return candidates, skipped


def run_interactive_deep_note_pick(
    *,
    window: Window,
    corpus_root: Path,
    public_dir: Path,
    picks_root: Path,
    inbox_dir: Path,
    config: GeneratorConfig,
    writer_factory: WriterFactory,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> DeepNotePickRun:
    brief_path = public_brief_path(public_dir, window)
    if not brief_path.exists():
        raise FileNotFoundError(
            f"public brief missing: {brief_path}; run `rexy publish --end {window.end.isoformat()}` first"
        )

    output_fn(f"Public brief: {brief_path}")
    output_fn("Open/glance this file before candidate review.")
    if not _ask_yes_no("Continue to candidate review? [y/n]: ", input_fn, output_fn):
        return DeepNotePickRun(window=window, picks_file=picks_path(picks_root, window), item_ids=[], written=[], skipped_existing=[])

    candidates, skipped = collect_deep_note_candidates(window, corpus_root, config)
    for skip in skipped:
        output_fn(f"Skipped overview item: {skip.entry.item_id} — {skip.reason}")

    selected: list[DeepNoteCandidate] = []
    for index, candidate in enumerate(candidates, start=1):
        _print_candidate(index, len(candidates), candidate, output_fn)
        if _ask_yes_no("Generate deep note for this item? [y/n]: ", input_fn, output_fn):
            selected.append(candidate)
            if len(selected) >= MAX_DEEP_NOTE_PICKS:
                output_fn(f"Max picks reached ({MAX_DEEP_NOTE_PICKS}). Remaining candidates skipped.")
                break

    pick_file = picks_path(picks_root, window)
    if not selected:
        output_fn("No items selected.")
        output_fn(f"{pick_file} unchanged.")
        output_fn("No deep notes generated.")
        return DeepNotePickRun(window=window, picks_file=pick_file, item_ids=[], written=[], skipped_existing=[])

    item_ids = [candidate.entry.item_id for candidate in selected]
    _print_pick_diff(pick_file, item_ids, output_fn)
    output_fn("This will:")
    output_fn(f"1. overwrite {pick_file}")
    output_fn(f"2. generate {len(item_ids)} deep note(s)")
    output_fn(f"3. write output under {inbox_dir}")
    if not _ask_yes_no("Continue? [y/n]: ", input_fn, output_fn):
        output_fn("Cancelled. No files changed.")
        return DeepNotePickRun(window=window, picks_file=pick_file, item_ids=[], written=[], skipped_existing=[])

    writer = writer_factory()
    _write_picks_file(pick_file, window, item_ids)
    written, skipped_existing = _generate_selected_notes(
        selected,
        window,
        corpus_root,
        inbox_dir,
        writer,
        input_fn,
        output_fn,
    )
    return DeepNotePickRun(
        window=window,
        picks_file=pick_file,
        item_ids=item_ids,
        written=written,
        skipped_existing=skipped_existing,
    )


def _signal_reason(
    entry: SelectionEntry,
    item: Item,
    keywords: tuple[str, ...],
    topic_name: str,
) -> str:
    topics = {topic.strip().lower() for topic in entry.topics}
    if topic_name.lower() in topics:
        return f"{topic_name} topic"
    haystack = _eligibility_haystack(entry, item)
    for keyword in keywords:
        if keyword.lower() in haystack:
            return f"keyword: {keyword}"
    return ""


def _eligibility_haystack(entry: SelectionEntry, item: Item) -> str:
    return " ".join([
        item.title,
        item.author,
        item.type,
        " ".join(item.topics_raw),
        entry.tldr_en,
        " ".join(entry.takeaways_en),
        entry.implication_en,
        " ".join(entry.topics),
    ]).lower()


def _print_candidate(index: int, total: int, candidate: DeepNoteCandidate, output_fn: OutputFn) -> None:
    entry = candidate.entry
    item = candidate.item
    output_fn("")
    output_fn(f"[{index}/{total}] {entry.item_id}")
    output_fn(f"Title: {item.title}")
    output_fn(f"Author: {item.author}")
    output_fn(f"Type: {item.type}")
    output_fn(f"Date: {item.published_at.isoformat()}")
    output_fn(f"Score: {entry.scores.composite:.1f}")
    output_fn(f"Topics: {', '.join(entry.topics) if entry.topics else '(none)'}")
    output_fn(f"Why eligible: {candidate.ai_reason}; {candidate.sim_reason}")
    output_fn(f"TL;DR: {entry.tldr_en}")
    if candidate.payload_chars:
        output_fn(f"Payload: extract available, {candidate.payload_chars} chars")
        output_fn("Deep-note risk: normal.")
    else:
        output_fn("Payload: metadata only / no payload")
        output_fn("Deep-note risk: high; note may be thin.")


def _ask_yes_no(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> bool:
    while True:
        answer = input_fn(prompt).strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False
        output_fn("Please answer y or n.")


def _print_pick_diff(path: Path, new_ids: list[str], output_fn: OutputFn) -> None:
    if path.exists():
        existing = _read_existing_item_ids(path)
        output_fn("")
        output_fn("Existing picks:")
        for item_id in existing:
            output_fn(f"- {item_id}")
        if not existing:
            output_fn("- (none)")
    output_fn("")
    output_fn("New picks:")
    for item_id in new_ids:
        output_fn(f"- {item_id}")


def _read_existing_item_ids(path: Path) -> list[str]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return []
    raw = data.get("item_ids")
    if not isinstance(raw, list):
        return []
    return [str(item_id) for item_id in raw if isinstance(item_id, str)]


def _write_picks_file(path: Path, window: Window, item_ids: list[str]) -> None:
    generated_at = now_utc().isoformat().replace("+00:00", "Z")
    lines = [
        "# Generated by rexy deep-notes pick. Do not edit manually.",
        f'window = "{window}"',
        f'generated_at = "{generated_at}"',
        f'source = "{PICKS_SOURCE}"',
        "item_ids = [",
    ]
    lines.extend(f'  "{item_id}",' for item_id in item_ids)
    lines.append("]")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _generate_selected_notes(
    selected: list[DeepNoteCandidate],
    window: Window,
    corpus_root: Path,
    inbox_dir: Path,
    writer: DeepNoteWriter,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> tuple[list[Path], list[Path]]:
    payloads = PayloadsStore(corpus_root / "payloads")
    inbox_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    skipped_existing: list[Path] = []

    for candidate in selected:
        item = candidate.item
        out = inbox_dir / f"deep_{safe_filename_part(item.id)}_{window.end.isoformat()}.md"
        if out.exists():
            action = _ask_existing_note_action(out, input_fn, output_fn)
            if action == "s":
                skipped_existing.append(out)
                output_fn(f"Skipped existing note: {out}")
                continue
            if action == "c":
                out = _copy_path(out)

        payload_text = ""
        if item.payload_ref and payloads.exists(item.payload_ref):
            payload_text = payloads.read(item.payload_ref)
        md = writer.write(
            item_id=item.id,
            item_type=item.type,
            source=_source_label(item),
            title=item.title,
            author=item.author,
            url=item.canonical_url,
            payload=payload_text,
        )
        md = prepare_deep_note_markdown(md)
        md = _confirm_opening_section(md, input_fn, output_fn)
        out.write_text(md.rstrip() + "\n", encoding="utf-8")
        written.append(out)
        output_fn(f"Wrote deep note: {out}")
    return written, skipped_existing


def _ask_existing_note_action(path: Path, input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn("")
    output_fn(f"Deep note already exists: {path}")
    if _ask_yes_no("Overwrite existing deep note? [y/n]: ", input_fn, output_fn):
        return "o"
    if _ask_yes_no("Create a suffixed copy instead? [y/n]: ", input_fn, output_fn):
        return "c"
    return "s"


def _copy_path(path: Path) -> Path:
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not find available copy filename for {path}")


def _confirm_opening_section(md: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    section = _extract_section(md, "### 00｜为什么在意这篇")
    output_fn("")
    output_fn("Draft section 00:")
    output_fn(section.rstrip())
    if _ask_yes_no("Accept section 00? [y/n]: ", input_fn, output_fn):
        return md

    output_fn("Paste replacement bullets or full section 00 Markdown.")
    output_fn("Finish with a single '.' line.")
    replacement_lines: list[str] = []
    while True:
        line = input_fn("> ")
        if line.strip() == ".":
            break
        replacement_lines.append(line.rstrip())
    replacement = "\n".join(replacement_lines).strip()
    if not replacement:
        raise ValueError("section 00 replacement is empty")
    if not replacement.startswith("### 00｜为什么在意这篇"):
        replacement = "### 00｜为什么在意这篇\n\n" + replacement
    updated = _replace_section(md, "### 00｜为什么在意这篇", replacement.rstrip() + "\n")
    return prepare_deep_note_markdown(updated)


def _extract_section(md: str, heading: str) -> str:
    start = md.find(heading)
    if start < 0:
        raise ValueError(f"missing section: {heading}")
    next_delimiter = md.find("\n---\n", start + len(heading))
    if next_delimiter < 0:
        return md[start:].rstrip()
    return md[start:next_delimiter].rstrip()


def _replace_section(md: str, heading: str, replacement: str) -> str:
    start = md.find(heading)
    if start < 0:
        raise ValueError(f"missing section: {heading}")
    next_delimiter = md.find("\n---\n", start + len(heading))
    if next_delimiter < 0:
        return md[:start] + replacement
    return md[:start] + replacement.rstrip() + md[next_delimiter:]


def _source_label(item: Item) -> str:
    labels = {
        "arxiv": "arXiv",
        "rss": "RSS",
        "podcast": "Podcast",
        "youtube": "YouTube",
        "blog": "Blog",
    }
    raw = str(item.source_type.value if hasattr(item.source_type, "value") else item.source_type)
    return labels.get(raw, raw)
