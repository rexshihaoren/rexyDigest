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
config/sources/*.toml                                       Weekly_Gist/Weekly_Brief_*.md
```

- **Ingest** runs Source Adapters (`config/sources/*.toml`), normalises
  results to **Items**, persists payloads, and writes per-run provenance.
- **Generate** runs a five-stage hybrid ranker (deterministic Python +
  per-Item LLM calls), writes a **Selection** JSONL plus a Markdown gist.
- **Publish** renders the Selection into the bilingual public **Brief**;
  it is LLM-free because translations were already written by the generator.
- Human-readable render contracts live in [`docs/templates/`](docs/templates/);
  Python renderers remain the runtime source of truth.

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

Defaults to the latest ingestion run's window. With the production default
config, `generate` calls DeepSeek per-Item; `--llm gemini` calls Gemini
per-Item; `--llm memory` runs the deterministic fixture for smoke tests.
For DeepSeek, put `DEEPSEEK_API_KEY=...` in repo-root `.env.local`.
For Gemini, put `GEMINI_API_KEY=...` in repo-root `.env.local`.
Writes `corpus/selections/Selection_<end>.jsonl`
and `Weekly_Gist/Weekly_Gist_<end>.md`. The internal gist's
`Top Items for Rex Ren` table includes an `ItemID` column so deep-note picks
can be copied without opening the JSONL.

### Publish

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy publish --window 2026-05-04/2026-05-11
```

Renders the Selection JSONL into a deterministic bilingual Brief beside the
Gist at `Weekly_Gist/Weekly_Brief_<end>.md`. No LLM calls.

### Review latest automated run

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy review latest
```

Runs `git pull --ff-only`, then opens the newest verified Review Package under
`Weekly_Gist/Review_Packages/<end>/<run-id>/`. Obsidian's periodic pull keeps
the same Git-tracked packages up to date. The package supplies the exact
Selection, Items, Payloads, Provenance, generator configuration, Gist, and
Brief from one run; it never merges into the machine-local `corpus/`.
Workspace-only edits and generated DeepNote drafts live under
`.rexy/reviews/<run-id>/`. The offline UI lets you read the Gist, edit the
Brief, and select 0–2 DeepNotes. Selected DeepNotes open in the existing strict
Markdown/visual review pages. **Finish Review** succeeds only after selected
DeepNotes reach `KnowledgeCard_Inbox/`, then writes
`KnowledgeCard_Inbox/weekly_brief_<end>.md`. Existing reviewed outputs are
never overwritten.

**KOL prioritization.** Each feed (RSS or YouTube) can declare `kol = "<slug>"` in its TOML
entry. Items from that feed get a `kol:<slug>` topic marker; the generator's prefilter lets
them through even with zero AGENT/SIM keyword hits, and prerank applies the configured
`kol_priors` boost (see [config defaults](python/rexy/generate/config.py)).

### Deep notes (optional, second LLM pass)

After `generate` + `publish`, run the interactive picker:

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy deep-notes pick --end 2026-05-11
```

The picker requires the weekly Brief for that date, shows Top 3 overview
AI×Simulation candidates one by one, writes a generated local audit file under
`corpus/deep_picks/`, and stages each confirmed note under `corpus/deep_notes/`.
It then opens a local review page. The staged Markdown remains readable and
editable; only **Finish review** writes the reviewed note to
`KnowledgeCard_Inbox/`. Deep notes use Gemini for the scarce editorial-quality
pass and must follow the strict KnowledgeCard contract in
[`docs/templates/deep_note.md`](docs/templates/deep_note.md).

For a YouTube Item, the same picker preserves the original YouTube URL, aligns
timestamped transcript evidence to each DeepNote section, and generates pending
keyframe candidates under `assets/visuals/`. Internal candidate state—including
source URL, timestamp URL, reason, and approval status—lives under
`corpus/visuals/`. This optional enrichment requires `yt-dlp` and `ffmpeg` on
`PATH`; missing tools or unavailable video leave text generation usable and
report visual enrichment as incomplete.

Resume an interrupted review without regenerating the note:

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy deep-notes review \
  --end 2026-05-11 --item-id '<item-id>'
```

The review page autosaves visual choices. Edited Markdown is evaluated only
after **Save changes**; affected visual decisions become stale and are judged
again. **No visual** is a valid reviewed outcome. If visual enrichment failed,
an explicit text-only waiver permits publishing. **Close** never publishes.

### Status

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy status
```

Prints corpus item counts by source type and the latest ingestion window.

### Parity check (optional diff vs Node)

```bash
PYTHONPATH=python ./.venv/bin/python -m rexy parity \
  --node    Weekly_Gist/<node-output>.md \
  --python  Weekly_Gist/<python-output>.md
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
| `.env.local`                    | `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`                              |

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
