"""Manual picks → second-pass LLM → one Markdown file per Item."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..corpus.items_store import ItemsStore
from ..corpus.payloads_store import PayloadsStore
from ..corpus.selections_store import SelectionsStore
from ..domain import Item, Window
from .deep_picks import load_deep_picks, picks_path as deep_picks_toml_path
from .llm.deep_note import DeepNoteWriter, MemoryDeepNoteWriter, safe_filename_part


@dataclass(slots=True)
class DeepNotesRun:
    window: Window
    picks_file: Path
    written: list[Path]


def run_deep_notes(
    window: Window,
    corpus_root: Path,
    picks_root: Path,
    inbox_dir: Path,
    writer: DeepNoteWriter,
) -> DeepNotesRun:
    picks_file = deep_picks_toml_path(picks_root, window)
    item_ids = load_deep_picks(picks_file)
    if not item_ids:
        return DeepNotesRun(window=window, picks_file=picks_file, written=[])

    selections = SelectionsStore(corpus_root / "selections")
    sel_path = selections.root / f"Selection_{window.end.isoformat()}.jsonl"
    selected = selections.read(window)
    allowed = {e.item_id for e in selected}
    for iid in item_ids:
        if iid not in allowed:
            raise ValueError(
                f"item_id {iid!r} not in Selection for {window.end} ({sel_path})"
            )

    items_store = ItemsStore(corpus_root / "items.jsonl")
    items_by_id = {it.id: it for it in items_store.read_all()}
    payloads = PayloadsStore(corpus_root / "payloads")

    inbox_dir.mkdir(parents=True, exist_ok=True)
    end_s = window.end.isoformat()
    written: list[Path] = []

    for iid in item_ids:
        item = items_by_id.get(iid)
        if item is None:
            raise ValueError(f"item_id {iid!r} not found in corpus items.jsonl")
        payload_text = _read_payload(item, payloads)
        md = writer.write(
            item_id=item.id,
            item_type=item.type,
            title=item.title,
            author=item.author,
            url=item.canonical_url,
            payload=payload_text,
        )
        fname = f"deep_{safe_filename_part(iid)}_{end_s}.md"
        out = inbox_dir / fname
        out.write_text(md.rstrip() + "\n", encoding="utf-8")
        written.append(out)

    return DeepNotesRun(window=window, picks_file=picks_file, written=written)


def _read_payload(item: Item, payloads: PayloadsStore) -> str:
    if not item.payload_ref:
        return ""
    if not payloads.exists(item.payload_ref):
        return ""
    return payloads.read(item.payload_ref)


def make_deep_note_writer(llm: str, model: str) -> DeepNoteWriter:
    if llm == "gemini":
        from .llm.deep_note import GeminiDeepNoteWriter

        return GeminiDeepNoteWriter(model=model)
    return MemoryDeepNoteWriter()
