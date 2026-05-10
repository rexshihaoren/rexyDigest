# Weekly Gist / Brief – Setup & Usage

## Environment
- Put your Google Gemini API key in a local env file:
  - Location: `.env.local`
  - Variable: `GEMINI_API_KEY=<your_key>`
  - Loaded by the scripts with precedence over `.env` (see [generate_gist.mjs](scripts/generate_gist.mjs) and [publize_brief.mjs](scripts/publize_brief.mjs)).
- Optional variables:
  - `STRICT_ENV=1` → fail fast only when the key is missing (network/model errors still fall back to stub or source text).
  - `MODEL_FALLBACKS=gemini-2.5-flash-lite,gemini-2.5-flash,gemini-2.5-pro,gemini-2.0-flash-001`

## Generate a Weekly Gist
- Command:
  - `node scripts/generate_gist.mjs`
- Date override (end of window):
  - `END_DATE=YYYY-MM-DD node scripts/generate_gist.mjs`
  - or `TARGET_DATE=YYYY-MM-DD`
- Output:
  - `Weekly_Gist/Weekly_Gist_<YYYY-MM-DD>.md` (see [generate_gist.mjs](scripts/generate_gist.mjs))

## Publish a Public Weekly Brief
- Default (uses the latest gist by mtime):
  - `node scripts/publize_brief.mjs`
- Target a specific gist:
  - `DIGEST_FILE=Weekly_Gist/Weekly_Gist_YYYY-MM-DD.md node scripts/publize_brief.mjs`
- Output directory:
  - Default `PUBLIC_DIR=Weekly_Gist/Public` (see [publize_brief.mjs](scripts/publize_brief.mjs))
  - File name: `Weekly_Brief_Public_<YYYY-MM-DD>.md` (see [publize_brief.mjs](scripts/publize_brief.mjs))

## About tmp-public-* folders
- Test runs and ad‑hoc local runs sometimes set `PUBLIC_DIR` to a temporary folder (e.g. `tmp-public-XXXXX`) for isolation and easy cleanup.
- Integration tests explicitly create such temp directories (see [publize_structured.test.mjs](tests/integration/publize_structured.test.mjs)).
- You can safely remove any `tmp-public-*` directories after inspection; for persistent outputs use the default `Weekly_Gist/Public`.

## Notes
- If the API key is missing or model calls fail, the generator/publisher will fall back to stub or source text so the pipeline remains testable.
- For model-backed transformations, ensure `GEMINI_API_KEY` is present in `.env.local`.

## Roadmap / TODO
- Add ingestion layer for real sources (RSS/YouTube/podcasts/arXiv/blogs) and feed items into the generator for ranking/summarization.
- Python migration (staged): Phase 1 Ingestion (Python) → items.jsonl + provenance; Phase 2 Generator (Python) → render Weekly_Gist, keep Node publisher; Phase 3 Publisher (Python) → parity tests, deprecate Node.
- Improve determinism: set temperature=0 in generator, allow pinning a single model, add date-based cache with `FORCE=1` override.
- Provenance: keep per-run meta (model, window, counts) and optional per-item URL validation log.
- Publisher hygiene: opt-in cleanup for `tmp-public-*` on success is implemented via `CLEAN_TMP_PUBLIC=1`; make it default in CI.
- Tests: add fixtures for ingestion, E2E tests for date overrides and bilingual strict formatting.
- Docs: expand setup for ENV variables and common workflows; link to Issues/Project board for task tracking.

Best practice: keep README’s roadmap short and stable; track detailed, actionable tasks in Issues/Projects and optionally maintain a dedicated `ROADMAP.md` for longer-term planning.***
