# Hybrid five-stage ranker

Today the LLM does filter, score, rank, dedupe, and summarise in a single prompt. **Novelty** in particular cannot be done well in-prompt because the LLM has no **Corpus** visibility — it confabulates rather than checking what was already covered. We adopt a five-stage pipeline that puts each concern in the place that can do it correctly:

1. **Pre-filter** (Python, in-process): drop out-of-**Window** Items, drop those with `payload_kind=unavailable` and no usable metadata, drop below a coarse keyword threshold against `KEYWORDS_AGENT ∪ KEYWORDS_SIM`.
2. **Pre-rank / shortlist** (Python, in-process): score on `Recency × KOL-prior × keyword-hit-density`. Take top ~30.
3. **Per-Item summarise-and-score** (LLM, parallel calls): given title + payload + lens, produce `{relevance, actionability, tldr, takeaways, implication, topics}`. LLM is an injected port; tests use a recorded-fixture adapter.
4. **Novelty score** (Python, in-process): `time-since-published × Corpus-distance` (no similar Item in last 4 weeks → high novelty). Reads the Corpus directly.
5. **Finalise** (Python, in-process): `composite = 0.4*relevance + 0.3*novelty + 0.3*actionability`, sort, take final top N (5–10), write the **Selection**.

## Considered options

- **Single-prompt LLM (current)** — rejected: no Corpus visibility means Novelty is structurally broken; debuggability is poor.
- **Fully deterministic scoring** — rejected: the Relevance lens ("Reality = computable simulation; AI+markets = reality-code manipulators") is too specific for keyword/embedding-only scoring; LLM judgment is genuinely better here.

## Consequences

- LLM cost is bounded and predictable: ~30 small calls per run instead of one giant call.
- Per-Item LLM responses are cache-keyable by `(item_id, model_version, prompt_version)`; re-running a Window with the same versions is effectively free.
- Each stage is a separately-testable module; deleting any stage causes a specific, named regression rather than vague quality loss.
- Tunable weights (the 0.4/0.3/0.3) remain in the prompt for now; lifting them into config is deferred until A/B comparisons demand it.

## Deferred (intentionally)

- Embedding-based pre-rank — start with naive keyword counting; upgrade only if quality demands it.
- LLM-call cache — implementation detail of Phase 2; not architectural.
