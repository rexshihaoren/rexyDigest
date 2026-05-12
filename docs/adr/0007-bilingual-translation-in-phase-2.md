# Bilingual translation in Phase 2 generator, not Phase 3 publisher

Translation moves from the publisher (today) to the generator. The Phase 2 LLM call that summarises and scores each shortlisted Item also produces Simplified Chinese fields; these are written into the **Selection** entry's `translations` sub-object (`title_zh`, `tldr_zh`, `takeaways_zh`, `implication_zh`, `topics_zh`). The Phase 3 Python publisher does no translation — it is pure rendering of an already-bilingual **Selection**.

## Why

- Today's pipeline is asymmetric: Section C of the gist is generated bilingually by the prompt; Sections A/B are translated post-hoc by the publisher; the **Brief** stitches them together inconsistently.
- Centralising translation in Phase 2 makes the **Selection** the single source of truth for all bilingual content and lets the Phase 3 publisher be a deterministic, LLM-free renderer.
- Per-Item LLM calls are already cache-keyable by `(item_id, model_version, prompt_version)` (see [ADR-0004](0004-hybrid-five-stage-ranker.md)); translations ride that cache for free.
- Failed translation is detected at Selection-write time, not at publish time — earlier feedback.

## Consequences

- Phase 3 publisher has no Gemini dependency, no `MODEL_FALLBACKS` config to maintain, and no failure mode that requires re-running the LLM. Smaller, faster, more deterministic.
- Parity testing in Stage 4 reduces to JSONL-equivalence + deterministic-render-equivalence, with no LLM noise.
- The translation legacy in [`scripts/publize_brief.mjs:208-229`](../../scripts/publize_brief.mjs) (`translate`) and [`scripts/publize_brief.mjs:662-684`](../../scripts/publize_brief.mjs) (`translateStructured`) is not ported.
