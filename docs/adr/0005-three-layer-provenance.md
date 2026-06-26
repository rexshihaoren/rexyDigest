# Three-layer Provenance

Re-runs, debugging "why was this Item included", and parity testing all need provenance close to the data they describe. We record provenance at three levels: per-**Item** (`fetched_at`, `adapter`, `schema_version`), per-**Selection** entry (`model`, `generated_at`), and per-**Run** (`corpus/runs/Run_<run_id>.json` written atomically per ingestion or generation run). This keeps each artefact self-describing without forcing every consumer to join across files for routine inspection.

## Consequences

- A bad ingestion run can be discarded by deleting one `Run_<id>.json` and the affected Items (identifiable by `adapter` + `fetched_at` window) — no global rebuild required.
- Phase 2 generator runs and Phase 1 ingestion runs each write their own Run file; they share a `window` field as the join key when needed.
- Provenance fields are required, not optional — adapters and generators that omit them are bugs.
