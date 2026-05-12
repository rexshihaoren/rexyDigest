# Parked work and deferred decisions

Single place for “we agreed to skip this for now.” Update when something ships or is cancelled.

## Closing the `python-migration` branch (ops checklist)

Implementation is done; **merge and branch deletion** are process steps on your machine:

1. **Commit** on `python-migration`: ADRs, `CONTEXT.md`, `docs/PARKED.md`, `README.md`, `.gitignore`, `python/rexy/**`, `python/tests/**`, `config/sources/*.toml` — **do not** commit `corpus/` (see `.gitignore`).
2. **Run** `PYTHONPATH=python .venv/bin/python -m pytest python/tests/ -q` and a smoke **`rexy ingest`** / **`rexy generate --llm memory`** if you want CI parity locally.
3. **Open PR** → `main`, get review, merge. *(Editorial gaps below — e.g. per-item blog notes, publicized Public brief — may defer merge even when CI and commit/push are fine.)*
4. **After merge**: delete branch `python-migration` (local + remote). Optional tag e.g. `python-pipeline-v0.1`.
5. **Node removal** stays separate: only when you manually trust output ([ADR-0002](adr/0002-node-publisher-stays-through-phase-2.md)); then one PR deleting `scripts/`, `package.json`, and Node `tests/`.

## Architecture / ingestion (from ADRs and design)

| Item | Notes |
|------|--------|
| **YouTube adapter + transcripts** | [ADR-0003](adr/0003-source-adapter-port.md): after inaugural `arxiv` + `rss`; transcripts best-effort, `metadata_only` if missing. |
| **Cross-source dedup** | Same content under `youtube:…` vs `rss:…` stays as two Items until optional `merged_into` (ADR-0003). |
| **Auto-generate `config/sources/*.toml` from a master KOL list** | Manual per-source configs first (ADR-0003). |
| **Embedding-based pre-rank** | [ADR-0004](adr/0004-hybrid-five-stage-ranker.md): start with keyword hits; upgrade only if needed. |
| **Per-Item LLM response cache** | [ADR-0004](adr/0004-hybrid-five-stage-ranker.md): implementation detail, not decided. |

## Quality and deprecation (editorial / product)

| Item | Notes |
|------|--------|
| **Per-item blog notes** | Richer notes per blog item (beyond current gist bullets) — **missing**; parked. |
| **Public brief conversion / publicized version** | Full digest → **Public/** “publicized” brief polish — **not done**; parked. |
| **Simple UI for manual quality review** | Rex needs a lightweight way to skim Selection + rendered Brief/Gist before ship. Not started. |
| **Judge LLM for quality gates** | Later automation to score faithfulness / hallucination risk vs sources; not started. |
| **Structural parity vs Node (`rexy parity`)** | Optional diff tool when comparing legacy Node output to Python output. **Not** a merge gate: legacy digests hallucinate; parity to them is not a quality bar ([ADR-0002](adr/0002-node-publisher-stays-through-phase-2.md)). |

## Ops

| Item | Notes |
|------|--------|
| **Remove Node `scripts/` + Node tests** | After manual sign-off on Python pipeline quality ([ADR-0002](adr/0002-node-publisher-stays-through-phase-2.md)); no fixed week count. |
| **arXiv 429 / rate limits** | `arxiv` client may return HTTP 429 on cold runs; tune delays, retries, or smaller `max_results` in `config/sources/arxiv.toml` ([ADR-0003](adr/0003-source-adapter-port.md) defers concurrency policy). |

## Local dev (PEP 668)

Homebrew Python often blocks `pip install` globally. Use a venv (see [README](../README.md) **Setup**): `python3 -m venv .venv` then `.venv/bin/pip install -r requirements.txt` before `pytest` / `rexy`.

`python/tests/test_rss_adapter.py` patches `rss_adapter.parse_feed_document` with a **stdlib-only Atom stub** so those two tests pass even when `feedparser` is missing (e.g. bare `python3 -m pytest`). **Production `rexy ingest` still requires `feedparser`** — keep it in `requirements.txt` and the venv.
