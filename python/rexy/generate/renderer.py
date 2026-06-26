"""Markdown gist renderer.

Per ADR-0002 the Phase-2 generator emits two artefacts in lockstep:
  - `corpus/selections/Selection_<end>.jsonl`  (truth)
  - `Weekly_Gist/Weekly_Gist_<end>.md`         (render the Node publisher consumes)

Per ADR-0008 there is no normaliser pass — this renderer IS the strict
format. The shape matches what `scripts/publize_brief.mjs:parseItemsFromBrief`
expects (see `scripts/lib/parser.mjs` for the exact regex contracts).
"""

from __future__ import annotations

from collections.abc import Iterable

from ..domain import Item, SelectionEntry, Window


def render_gist(
    window: Window,
    entries: Iterable[SelectionEntry],
    items_by_id: dict[str, Item],
) -> str:
    """Return the full Markdown gist for one Selection."""

    entries_list = list(entries)
    paper_count = sum(
        1 for e in entries_list
        if items_by_id.get(e.item_id) and items_by_id[e.item_id].type == "paper"
    )

    lines: list[str] = []
    lines.append(f"# Weekly Gist – {window.end.isoformat()}")
    lines.append("")
    lines.append("# WEEKLY BRIEF")
    lines.append("")
    lines.append(
        f"**COVERAGE_WINDOW: {window.start.isoformat()} – {window.end.isoformat()} "
        f"| Items found {len(entries_list)} | Papers {paper_count}**"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    for entry in entries_list:
        item = items_by_id.get(entry.item_id)
        if item is None:
            # corpus inconsistency — render a stub line so the count still matches
            lines.append(f"*   **(missing item {entry.item_id})**")
            lines.append("")
            continue
        lines.extend(_render_item_block(entry, item))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.extend(_render_table(entries_list, items_by_id))

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_item_block(entry: SelectionEntry, item: Item) -> list[str]:
    """One '* KOL — Title (Type) — Date — [URL](URL)' block plus sub-bullets."""

    item_type_label = _human_type(item.type)
    topics_str = ", ".join(entry.topics) if entry.topics else "Agent"

    head = (
        f"*   **{_safe(item.author)}** — {_safe(item.title)} ({item_type_label}) "
        f"— {item.published_at.isoformat()} "
        f"— [{item.canonical_url}]({item.canonical_url})"
    )
    tldr = f"    *   **TL;DR:** {entry.tldr_en.strip()}"
    takeaways_text = " ".join(_normalise_takeaway(t) for t in entry.takeaways_en)
    takeaways = f"    *   **Takeaways:** {takeaways_text}"
    impl = f"    *   **Implication for Rex Ren:** {entry.implication_en.strip()}"
    composite = (
        f"    *   **CompositeScore ({entry.scores.composite:.1f}) "
        f"| Topics: {topics_str}**"
    )
    return [head, tldr, takeaways, impl, composite]


def _normalise_takeaway(s: str) -> str:
    s = s.strip().rstrip(".")
    if not s:
        return ""
    return s + "."


def _human_type(item_type: str) -> str:
    return {
        "paper": "Paper",
        "blog": "Blog",
        "podcast": "Podcast",
        "video": "Video",
        "talk": "Talk",
    }.get(item_type, item_type.capitalize() or "Item")


def _safe(s: str) -> str:
    """Strip characters that would break the parser regex (em-dashes, brackets)."""
    return s.replace("|", "/").replace("\n", " ").strip()


def _render_table(
    entries: list[SelectionEntry],
    items_by_id: dict[str, Item],
) -> list[str]:
    if not entries:
        return []
    out = [
        "## Top Items for Rex Ren",
        "",
        "| ItemID | KOL | Title | Date | Topics | Type | Link | ReadPriority | ShortSummary | CompositeScore | Relevance | Novelty | Actionability |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in entries:
        item = items_by_id.get(entry.item_id)
        if item is None:
            continue
        prio = (
            "Must-Read" if entry.scores.composite >= 8.0
            else "Worth Skimming" if entry.scores.composite >= 6.0
            else "Archive"
        )
        topics_str = ", ".join(entry.topics) if entry.topics else "Agent"
        short = entry.tldr_en.strip().replace("|", "/")
        out.append(
            f"| {entry.item_id} "
            f"| {_safe(item.author)} "
            f"| {_safe(item.title)} "
            f"| {item.published_at.isoformat()} "
            f"| {topics_str} "
            f"| {_human_type(item.type)} "
            f"| {item.canonical_url} "
            f"| {prio} "
            f"| {short} "
            f"| {entry.scores.composite:.1f} "
            f"| {entry.scores.relevance:.1f} "
            f"| {entry.scores.novelty:.1f} "
            f"| {entry.scores.actionability:.1f} |"
        )
    return out
