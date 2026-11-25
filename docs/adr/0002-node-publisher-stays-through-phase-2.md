# Node publisher stays through Phase 2; deprecation when quality is trusted

**Status:** Migration complete. The Python pipeline renders the Gist and Brief from Selection data. The Node scripts, dependencies, and tests are retired.

The migration is staged: Phase 2 lands a Python generator before Phase 3 lands a Python publisher. To avoid a flag-day cutover, the Phase 2 generator emits BOTH a Markdown **Gist** (consumed by the existing Node publisher unchanged) AND a structured `corpus/selections/Selection_<end-date>.jsonl` (the eventual input to the Python publisher).

**Deprecation decision:** The cutover depended on manual review of the Python pipeline’s output. Structural comparison with legacy briefs was optional because matching their structure could not establish factual accuracy.

Planned follow-ups (see [`docs/PARKED.md`](../PARKED.md)): a **simple UI** for human review before publish, and later a **judge LLM** for automated quality checks.

## Consequences

- Phase 2's "output contract" is two artefacts, not one — but only one (the Markdown Gist) is consumed during Phase 2; the JSONL is written for Phase 3 and for inspection.
- The Python publisher reads the JSONL directly. The legacy Markdown parser was retired with Node.
- The optional `rexy parity` migration tool was retired alongside the Node publisher.
