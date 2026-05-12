# Node publisher stays through Phase 2; deprecation when quality is trusted

The migration is staged: Phase 2 lands a Python generator before Phase 3 lands a Python publisher. To avoid a flag-day cutover, the Phase 2 generator emits BOTH a Markdown **Gist** (consumed by the existing Node publisher unchanged) AND a structured `corpus/selections/Selection_<end-date>.jsonl` (the eventual input to the Python publisher).

**Deprecation gate (revised):** Node is removed only after **manual sign-off** that the Python pipeline’s output is good enough to ship — not after structural parity with the legacy Node publisher. Legacy Rexy digests are known to hallucinate; matching them would bake in bad behaviour. Optional: use `rexy parity` as a **diff aid** when comparing specific weeks, not as an automatic “N weeks OK” requirement.

Planned follow-ups (see [`docs/PARKED.md`](../PARKED.md)): a **simple UI** for human review before publish, and later a **judge LLM** for automated quality checks.

## Consequences

- Phase 2's "output contract" is two artefacts, not one — but only one (the Markdown Gist) is consumed during Phase 2; the JSONL is written for Phase 3 and for inspection.
- The Python publisher in Phase 3 reads the JSONL directly and never re-parses Markdown. The regex parsing logic in [`scripts/lib/parser.mjs`](../../scripts/lib/parser.mjs) and the inlined copies in [`scripts/publize_brief.mjs`](../../scripts/publize_brief.mjs) die with Node and are not ported.
- `rexy parity` remains a **structural** comparison tool (item counts, URLs, scores); it does not assert semantic quality or alignment with ground truth.
