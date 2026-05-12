# Rexy Digest – Setup & Usage

Weekly bilingual brief covering AI agents and the simulation hypothesis.

## Architecture

The pipeline is **three independent stages** wired through a structured
**Corpus** on disk. Stage decisions are recorded in `docs/adr/`; vocabulary
is in [`CONTEXT.md`](CONTEXT.md).

```
┌────────────┐   items.jsonl     ┌────────────┐   Selection_*.jsonl  ┌────────────┐
│  Ingest    │──────────────────▶│  Generate  │─────────────────────▶│  Publish   │
│ (Phase 1)  │   payloads/       │ (Phase 2)  │   Weekly_Gist_*.md   │ (Phase 3)  │
│  Python    │   runs/           │  Python    │                      │  Python    │
└────────────┘                   └────────────┘                      └────────────┘
       ▲                                                                     │
       │                                                                     ▼
config/sources/*.toml                                       Weekly_Gist/Public/Weekly_Brief_Public_*.md
```

- **Ingest** runs Source Adapters (`config/sources/*.toml`), normalises
  results to **Items**, persists payloads, and writes per-run provenance.
- **Generate** runs a five-stage hybrid ranker (deterministic Python +
  per-Item LLM calls), writes a **Selection** JSONL plus a Markdown gist.
- **Publish** renders the Selection into the bilingual public **Brief**;
  it is LLM-free because translations were already written by the generator.

See [`docs/adr/`](docs/adr/) for the load-bearing decisions
(`items.jsonl` as the contract, Source Adapter port, hybrid ranker,
three-layer provenance, etc.). Deferred and parked work lives in
[`docs/PARKED.md`](docs/PARKED.md).

## Setup

Use a **virtualenv** (Homebrew / PEP 668 Python blocks global `pip install`).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Do **not** rely on `python3 -m pip install -r requirements.txt` on the system interpreter: it fails with `externally-managed-environment` (PEP 668). Always install into `.venv` (or another venv) first.

For tests and CLI, prefer `.venv/bin/python` with `PYTHONPATH=python` (see **Tests** and **Usage** below).

Put your Gemini API key in `.env.local`:

```
GEMINI_API_KEY=...
```

## Usage

### Ingest

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy ingest --window 2026-05-04/2026-05-11
```

Defaults to a 7-day window ending today. Reads adapter configs from
`config/sources/*.toml`. Writes to `corpus/items.jsonl`,
`corpus/payloads/`, and `corpus/runs/Run_*.json`.

### Generate

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy generate --window 2026-05-04/2026-05-11
```

Defaults to the latest ingestion run's window. With `--llm gemini`
(default) calls Gemini per-Item; with `--llm memory` runs the deterministic
fixture for smoke tests. Writes `corpus/selections/Selection_<end>.jsonl`
and `Weekly_Gist/Weekly_Gist_<end>.md`.

### Publish

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy publish --window 2026-05-04/2026-05-11
```

Renders the Selection JSONL into a deterministic bilingual public brief at
`Weekly_Gist/Public/Weekly_Brief_Public_<end>.md`. No LLM calls.

### Status

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy status
```

Prints corpus item counts by source type and the latest ingestion window.

### Parity check (optional diff vs Node)

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy parity \
  --node    Weekly_Gist/Public/<node-output>.md \
  --python  Weekly_Gist/Public/<python-output>.md
```

Compares **structural** fields (item set, composite scores, English blurbs)
between a legacy Node brief and a Python brief. Useful when diffing a
specific week; **not** a quality gate — legacy output can hallucinate. See
[`docs/PARKED.md`](docs/PARKED.md) for manual review UI and judge-LLM plans.

## Tests

```bash
PYTHONPATH=python .venv/bin/pytest python/tests/
```

## Legacy Node pipeline (deprecated)

The original Node-based generator and publisher live under `scripts/`:

- `scripts/generate_gist.mjs` — calls one LLM prompt to write the gist
- `scripts/publize_brief.mjs` — parses the gist back out with regex,
  re-translates with Gemini

These are **superseded** by the Python pipeline above. They remain until
you **manually** trust the Python pipeline for production (per
[ADR-0002](docs/adr/0002-node-publisher-stays-through-phase-2.md)) — not
after parity with legacy output. Then `scripts/`, `package.json`, and
`tests/` (Node) can be removed. Deferred UX: [`docs/PARKED.md`](docs/PARKED.md).

## Configuration

| File                            | Purpose                                                          |
|---------------------------------|------------------------------------------------------------------|
| `config/sources/*.toml`         | One file per Source Adapter instance (reserved keys: `source_type`, `disabled`) |
| `config/generator.toml` (opt.)  | Override generator defaults (KOL priors, weights, model)          |
| `.env.local`                    | `GEMINI_API_KEY`                                                  |

## Repo layout

```
python/rexy/                  # the Python package
  domain.py                   # Item, SelectionEntry, Window, Scores, ...
  ingest.py                   # ingestion orchestrator
  cli.py                      # `python -m rexy ...`
  sources/                    # Source Adapter port + arxiv/rss adapters
  corpus/                     # items_store, payloads_store, runs_store, selections_store
  generate/                   # 5-stage ranker + LLM port + gist renderer
  publish/                    # bilingual Selection → public-brief renderer
python/tests/                 # pytest suite (60+ tests)
config/sources/               # adapter configs
docs/adr/                     # load-bearing architectural decisions
CONTEXT.md                    # the shared vocabulary
scripts/                      # legacy Node pipeline (slated for removal)
```
