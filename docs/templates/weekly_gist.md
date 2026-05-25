# Weekly Gist Template

This is the human-readable contract for the current Python Weekly Gist renderer.
Runtime source of truth: `python/rexy/generate/renderer.py`.

The renderer is deterministic. This file is for human review, editorial
alignment, and template validation tests; it is not parsed at runtime.

## Output Path

`Weekly_Gist/Weekly_Gist_<end-date>.md`

## Structure

```md
# Weekly Gist – {end_date}

# WEEKLY BRIEF

**COVERAGE_WINDOW: {start_date} – {end_date} | Items found {item_count} | Papers {paper_count}**

---

*   **{author}** — {title} ({type_label}) — {published_date} — [{canonical_url}]({canonical_url})
    *   **TL;DR:** {tldr_en}
    *   **Takeaways:** {takeaway_1}. {takeaway_2}. {takeaway_3}.
    *   **Implication for Rex Ren:** {implication_en}
    *   **CompositeScore ({composite_score}) | Topics: {topics}**

---

## Top Items for Rex Ren

| ItemID | KOL | Title | Date | Topics | Type | Link | ReadPriority | ShortSummary | CompositeScore | Relevance | Novelty | Actionability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {item_id} | {author} | {title} | {published_date} | {topics} | {type_label} | {canonical_url} | {read_priority} | {tldr_en} | {composite_score} | {relevance} | {novelty} | {actionability} |
```

## Rules

- The Selection JSONL is the truth; this Markdown is a deterministic render.
- Item order follows Selection rank order.
- Every rendered item block has TL;DR, Takeaways, Implication, CompositeScore,
  and Topics.
- `Top Items for Rex Ren` includes `ItemID` so deep-note picks can be copied
  without opening JSONL.
- Missing corpus Items render as a visible missing-item stub in the brief body
  and are skipped in the table.
