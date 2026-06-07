# Parked work and deferred decisions

Single place for “we agreed to skip this for now.” Update when something ships or is cancelled.

## Closing the `python-migration` branch (ops checklist)

Implementation is done; **merge and branch deletion** are process steps on your machine:

1. **Commit** on `python-migration`: ADRs, `CONTEXT.md`, `docs/PARKED.md`, `README.md`, `.gitignore`, `python/rexy/**`, `python/tests/**`, `config/sources/*.toml` — **do not** commit `corpus/` (see `.gitignore`).
2. **Run** `PYTHONPATH=python .venv/bin/python -m pytest python/tests/ -q` (also **`.github/workflows/python-tests.yml`** on push when `python/**` changes) and a smoke **`rexy ingest`** / **`rexy generate --llm memory`** if you want CI parity locally.
3. **Open PR** → `main`, get review, merge. *(Editorial gaps below — e.g. per-item blog notes, publicized Public brief — may defer merge even when CI and commit/push are fine.)*
4. **After merge**: delete branch `python-migration` (local + remote). Optional tag e.g. `python-pipeline-v0.1`.
5. **Node removal** stays separate: only when you manually trust output ([ADR-0002](adr/0002-node-publisher-stays-through-phase-2.md)); then one PR deleting `scripts/`, `package.json`, and Node `tests/`.

## Architecture / ingestion (from ADRs and design)

| Item | Notes |
|------|--------|
| **YouTube `[[channels]]` — Rex manual hard-set** | First batch was **auto-generated** from `kol_priors` + `scripts/bootstrap_youtube_from_kols.py` (`YOUTUBE_SEED`). **Rex must verify** every `channel_id` / `default_author` / `kol` slug (handles can resolve to the wrong `browseId`). Re-run the script after editing `YOUTUBE_SEED`, or hand-edit `config/sources/youtube.toml`. Six KOL slugs still have **no** seed row: `lilian weng`, `tegmark`, `sean carroll`, `scott aaronson`, `nick bostrom`, `anil seth`. |
| **Cross-source dedup** | Same content under `youtube:…` vs `rss:…` stays as two Items until optional `merged_into` (ADR-0003). |
| **Auto-generate `config/sources/*.toml` from a master KOL list** | **Partial:** `scripts/bootstrap_youtube_from_kols.py` emits `youtube.toml` from `kol_priors` ∩ `YOUTUBE_SEED` (hand IDs). Rex must hard-verify each channel row (see **YouTube `[[channels]]` — Rex manual hard-set** above). RSS stays manual. |
| **Embedding-based pre-rank** | [ADR-0004](adr/0004-hybrid-five-stage-ranker.md): start with keyword hits; upgrade only if needed. |
| **Per-Item LLM response cache** | [ADR-0004](adr/0004-hybrid-five-stage-ranker.md): implementation detail, not decided. |

## Quality and deprecation (editorial / product)

| Item | Notes |
|------|--------|
| **Per-item blog notes** | **Shipped**: long-form deep dives — interactive AI×Simulation picks from public Top 3 overview → `rexy deep-notes pick` → generated audit TOML under `config/deep_picks/` + `KnowledgeCard_Inbox/*.md`. Narrative polish still optional. |
| **Agentic taste-learning picker** | Parked. Current deep-note picks require Rex's interactive `y/n` taste decisions. A future agentic flow may learn those preferences, but it must be explicit and reviewable. |
| **Public brief 每周雷达 polish** | **Shipped**: bilingual 本周亮点 lead block + 本周 KOL roster footer in `python/rexy/publish/renderer.py`. Further narrative polish (e.g. cross-item synthesis paragraphs) parked. |
| **Simple UI for manual quality review** | Rex needs a lightweight way to skim Selection + rendered Brief/Gist before ship. Not started. |
| **Judge LLM for quality gates** | Later automation to score faithfulness / hallucination risk vs sources; not started. |
| **Structural parity vs Node (`rexy parity`)** | Optional diff tool when comparing legacy Node output to Python output. **Not** a merge gate: legacy digests hallucinate; parity to them is not a quality bar ([ADR-0002](adr/0002-node-publisher-stays-through-phase-2.md)). |

## Ops

| Item | Notes |
|------|--------|
| **Remove Node `scripts/` + Node tests** | After manual sign-off on Python pipeline quality ([ADR-0002](adr/0002-node-publisher-stays-through-phase-2.md)); no fixed week count. |
| **arXiv 429 / rate limits** | `arxiv` client may return HTTP 429 on cold runs; tune delays, retries, or smaller `max_results` in `config/sources/arxiv.toml` ([ADR-0003](adr/0003-source-adapter-port.md) defers concurrency policy). |

## Rex — queued decisions (parked 2026-05-14)

Agent pass (~30m): consolidated YouTube bootstrap into `python/rexy/sources/youtube_bootstrap.py`, added `python/tests/test_youtube_bootstrap.py`, `.github/workflows/python-tests.yml`, and reordered `config/sources/youtube.toml` to **`kol_priors` key order** (same bytes as `render_youtube_toml`). **You choose:**

| # | Topic | Options / notes |
|---|--------|-------------------|
| 1 | **CI Python version** | Workflow uses **3.12**; local `.venv` may be **3.14**. Align versions or keep matrix later. |
| 2 | **Weekly Gist GitHub Action** | `.github/workflows/weekly-gist.yml` is still **Node** (`generate_gist.mjs`). Migrate to `python -m rexy generate`, keep both, or leave as-is until Node removal. |
| 3 | **KOL ↔ org YouTube rows** | `harrison chase` → LangChain, `jerry liu` → LlamaIndex, `shane legg` → Google DeepMind: keep **org channel + personal `kol` slug**, or split slugs / drop org rows. |
| 4 | **Six missing `YOUTUBE_SEED` slugs** | Add verified `channel_id`s for `lilian weng`, `tegmark`, `sean carroll`, `scott aaronson`, `nick bostrom`, `anil seth`, or explicitly **RSS-only** and remove from YouTube expectations. |
| 5 | **`youtube.toml` source of truth** | Prefer always **`scripts/bootstrap_youtube_from_kols.py`** after editing `YOUTUBE_SEED`, or allow **hand-only** edits and drop script drift risk. |
| 6 | **Public brief “每周雷达” depth** | Lead + KOL roster shipped; add **weekly synthesis paragraph** (new LLM or hand), or leave minimal. |

## Local dev (PEP 668)

Homebrew Python often blocks `pip install` globally. Use a venv (see [README](../README.md) **Setup**): `python3 -m venv .venv` then `.venv/bin/pip install -r requirements.txt` before `pytest` / `rexy`.

`python/tests/test_rss_adapter.py` patches `rss_adapter.parse_feed_document` with a **stdlib-only Atom stub** so those two tests pass even when `feedparser` is missing (e.g. bare `python3 -m pytest`). **Production `rexy ingest` still requires `feedparser`** — keep it in `requirements.txt` and the venv.
