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
from .visual_review import GeminiVisualJudge, judge_candidates
from .video_visuals import (
    VisualEnrichmentResult,
    fetch_source_page,
    generate_section_keyframes,
    resolve_youtube_url,
    write_candidate_sidecar,
)

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


def weekly_brief_path(brief_dir: Path, window: Window) -> Path:
    return brief_dir / f"Weekly_Brief_{window.end.isoformat()}.md"


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
    brief_dir: Path,
    picks_root: Path,
    inbox_dir: Path,
    config: GeneratorConfig,
    writer_factory: WriterFactory,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> DeepNotePickRun:
    brief_path = weekly_brief_path(brief_dir, window)
    if not brief_path.exists():
        raise FileNotFoundError(
            f"weekly Brief missing: {brief_path}; run `rexy publish --end {window.end.isoformat()}` first"
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
        item_part = safe_filename_part(item.id)
        final_out = inbox_dir / f"deep_{item_part}_{window.end.isoformat()}.md"
        if final_out.exists():
            action = _ask_existing_note_action(final_out, input_fn, output_fn)
            if action == "s":
                skipped_existing.append(final_out)
                output_fn(f"Skipped existing note: {final_out}")
                continue
            if action == "c":
                final_out = _copy_path(final_out)

        draft = corpus_root / "deep_notes" / item_part / window.end.isoformat() / "draft.md"
        draft.parent.mkdir(parents=True, exist_ok=True)

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
        draft.write_text(md.rstrip() + "\n", encoding="utf-8")
        written.append(draft)
        output_fn(f"Wrote DeepNote draft: {draft}")
        _generate_visual_candidates(
            item, md, payload_text, window, corpus_root, draft, final_out, output_fn,
        )
    return written, skipped_existing


def _generate_visual_candidates(
    item: Item,
    markdown: str,
    payload: str,
    window: Window,
    corpus_root: Path,
    draft_path: Path,
    final_path: Path,
    output_fn: OutputFn,
) -> None:
    source_type = str(
        item.source_type.value if hasattr(item.source_type, "value") else item.source_type
    )
    has_video_marker = "full video" in payload.lower()
    item_part = safe_filename_part(item.id)
    visual_root = corpus_root / "visuals" / item_part / window.end.isoformat()
    sidecar = visual_root / "candidates.json"
    has_video_source = source_type == "youtube" or "youtube.com/" in payload or "youtu.be/" in payload or has_video_marker
    if not has_video_source:
        result = VisualEnrichmentResult(True, item.canonical_url, [])
        write_candidate_sidecar(result, sidecar)
        _annotate_review_sidecar(sidecar, item.id, draft_path, final_path)
        output_fn(f"No video enrichment required; review sidecar: {sidecar}")
        return

    source_url = resolve_youtube_url(item.canonical_url, payload, fetch_source_page)
    if source_url is None:
        result = VisualEnrichmentResult(False, item.canonical_url, [], "original YouTube URL not found")
        write_candidate_sidecar(result, sidecar)
        _annotate_review_sidecar(sidecar, item.id, draft_path, final_path)
        output_fn(f"Visual enrichment incomplete: original YouTube URL not found; sidecar: {sidecar}")
        return

    asset_root = corpus_root.parent / "assets" / "visuals" / item_part / window.end.isoformat()
    result = generate_section_keyframes(
        note_markdown=markdown,
        payload=payload,
        youtube_url=source_url,
        output_dir=asset_root,
    )
    write_candidate_sidecar(result, sidecar)
    _annotate_review_sidecar(sidecar, item.id, draft_path, final_path)
    if result.complete:
        if result.candidates:
            try:
                judge_candidates(draft_path, sidecar, GeminiVisualJudge())
            except RuntimeError as exc:
                _mark_visual_incomplete(sidecar, str(exc))
                output_fn(f"Visual judgment incomplete: {exc}; sidecar: {sidecar}")
                return
        output_fn(f"Visual candidates: {len(result.candidates)}; review sidecar: {sidecar}")
    else:
        output_fn(f"Visual enrichment incomplete: {result.error}; sidecar: {sidecar}")


def _annotate_review_sidecar(
    sidecar: Path,
    item_id: str,
    draft_path: Path,
    final_path: Path,
) -> None:
    import json

    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["item_id"] = item_id
    data["draft_path"] = str(draft_path)
    data["final_path"] = str(final_path)
    sidecar.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mark_visual_incomplete(sidecar: Path, error: str) -> None:
    import json

    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["complete"] = False
    data["error"] = error
    sidecar.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
