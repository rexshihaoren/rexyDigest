# Strict format is the default and only render; no normaliser

The Phase 3 Python publisher renders **Selection** JSONL directly into the strict-format **Brief**. The separate normalisation pipeline ([`scripts/lib/transform_strict.mjs`](../../scripts/lib/transform_strict.mjs) + [`scripts/batch_transform.mjs`](../../scripts/batch_transform.mjs) + parts of [`scripts/lib/markdown_utils.mjs`](../../scripts/lib/markdown_utils.mjs)) is **not ported**. Existing `*_strict.md` files in the repo remain as legacy artefacts but no new ones are produced after Phase 3 cutover.

## Why

The strict normaliser exists to defend against drift in the LLM-emitted Markdown. Under [ADR-0002](0002-node-publisher-stays-through-phase-2.md) the LLM no longer emits the final Markdown — the **Selection** JSONL is the truth and a deterministic Python renderer produces the Markdown. A deterministic renderer cannot drift from its template, so the normaliser has nothing to defend against.

## Consequences

- One render module, one format. No `*_strict.md` doublet files cluttering `Weekly_Gist/` going forward.
- Hand-edits to a Brief are not normalised back automatically — that's the editor's responsibility, not the pipeline's.
- The "strict format" specification becomes the property of the Phase 3 renderer and lives in code (one Python module) rather than as a normaliser run after the fact.
