# Strict format is the default and only render; no normaliser

The Phase 3 Python publisher renders **Selection** JSONL directly into the strict-format **Brief**. The separate normalisation pipeline ([`scripts/lib/transform_strict.mjs`](../../scripts/lib/transform_strict.mjs) + [`scripts/batch_transform.mjs`](../../scripts/batch_transform.mjs) + parts of [`scripts/lib/markdown_utils.mjs`](../../scripts/lib/markdown_utils.mjs)) is **not ported**. Existing `*_strict.md` files in the repo remain as legacy artefacts but no new ones are produced after Phase 3 cutover.

Human-readable render contracts live in [`docs/templates/`](../templates/):

- [`weekly_gist.md`](../templates/weekly_gist.md)
- [`public_brief.md`](../templates/public_brief.md)

Those Markdown files are for review and validation. Runtime rendering remains
in Python code.

## Why

The strict normaliser exists to defend against drift in the LLM-emitted Markdown. Under [ADR-0002](0002-node-publisher-stays-through-phase-2.md) the LLM no longer emits the final Markdown — the **Selection** JSONL is the truth and a deterministic Python renderer produces the Markdown. A deterministic renderer cannot drift from its template, so the normaliser has nothing to defend against.

## Consequences

- One render module, one format. No `*_strict.md` doublet files cluttering `Weekly_Gist/` going forward.
- Hand-edits to a Brief are not normalised back automatically — that's the editor's responsibility, not the pipeline's.
- The "strict format" implementation lives in Python renderer modules rather than as a normaliser run after the fact.
- The readable structure contract is mirrored in `docs/templates/` so humans can review it and tests can validate drift intentionally.
