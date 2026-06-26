# items.jsonl is the contract between Phase 1 and Phase 2

The current pipeline calls one LLM prompt to produce a Markdown gist, then the publisher parses Items back out of that Markdown with regex (`parseItemsFromBrief`). This is confabulation followed by reverse-engineering. We are introducing a structured **Corpus** (`corpus/items.jsonl` + `corpus/payloads/`) that Phase 1 ingestion writes to and Phase 2 generation reads from, so Items are real records rather than parsed-out artefacts and Phase 2 can summarise from real source text rather than invent it.

## Consequences

- Phase 2 generator is no longer a single prompt; it is a ranker + summariser that consumes the Corpus.
- Items are immutable across runs; per-run outputs (rankings, summaries, scores) live on **Selection** entries (see ADR-0002), not on Items themselves.
- The schema is versioned (`schema_version` on every Item) so future field changes are explicit migrations rather than silent drift.
