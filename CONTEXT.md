# Rexy Digest Context

The shared vocabulary for the Rexy Digest pipeline: ingesting content, selecting weekly highlights, and publishing bilingual briefs. Use these terms in code, docs, ADRs, and discussions — drift causes pain.

## Language

**Item**:
A real piece of published content (a video, paper, blog post, talk, podcast episode) with a stable upstream identity. Immutable once ingested.
_Avoid_: Article, entry, post, candidate.

**Source**:
An upstream system that publishes content (YouTube, arXiv, an RSS feed, a podcast feed, a blog).
_Avoid_: Provider, channel, origin (when meaning the system).

**Source Adapter**:
A module that fetches from one **Source** family and yields **Items** plus optional **Payload** bytes. Each adapter is self-configuring via `config/sources/<name>.toml`.
_Avoid_: Connector, plugin, fetcher.

**Payload**:
The raw text content of an **Item** (transcript, abstract, article body). Optional. Lives at `corpus/payloads/<id>.{txt,md}` rather than inline in `items.jsonl`.
_Avoid_: Body, content, full text.

**Payload Kind**:
An enum on every **Item** declaring what was actually obtained: `metadata_only | extract | full_text | unavailable`. Honest about what we have so the renderer never confabulates.
_Avoid_: Content type, payload type.

**Window**:
An inclusive date range a **Selection** covers, written as `YYYY-MM-DD/YYYY-MM-DD` (start/end). The end date is the run date by default.
_Avoid_: Period, date range, week, coverage.

**Selection**:
The act and result of picking **Items** from the **Corpus** for one **Window**, with per-Item scores and summaries. Materialised as `corpus/selections/Selection_<end-date>.jsonl`.
_Avoid_: Pick, brief items, ranking, results.

**Composite Score**:
A 1-decimal score per Selection entry, computed as `0.4*relevance + 0.3*novelty + 0.3*actionability`. The three sub-scores live alongside it.
_Avoid_: Score (alone), rating, rank.

**Gist**:
The internal Markdown document rendered from a **Selection** — `Weekly_Gist/Weekly_Gist_<end-date>.md`. Contains the full long-form content (today's prompt's Sections A/B/C) and exposes `ItemID` in the `Top Items for Rex Ren` table for manual deep-note picks.
_Avoid_: Digest, weekly, summary, internal brief.

**Brief**:
The public bilingual Markdown document derived from a **Gist** for publication — `Weekly_Gist/Public/Weekly_Brief_Public_<end-date>.md`.
_Avoid_: Public digest, weekly post, blog brief.

**Corpus**:
The persistent on-disk store of **Items**, **Payloads**, past **Selections**, and run-level **Provenance**. Single source of truth for everything the generator and publisher consume.
_Avoid_: Store, database, library, archive.

**Provenance**:
The recorded origin of any artifact: when it was fetched/generated, by which adapter or model version, with which config snapshot. Lives at three levels — per-Item, per-Selection, per-Run.
_Avoid_: Metadata, audit, history.

**KOL**:
A person or outlet (Karpathy, Latent Space, Lilian Weng) we want to monitor across one or more **Sources**. A curation aid only — the operational truth is each adapter's `config/sources/<name>.toml`. Not an executable concept.
_Avoid_: Author, channel, creator (those have other meanings here).

## Relationships

- A **Source Adapter** reads a **Source** and yields **Items** (plus optional **Payload**) into the **Corpus**.
- An **Item** has exactly one **Payload Kind**; if `extract` or `full_text`, it has one **Payload**.
- A **Selection** references many **Items** by `id` and lives in one **Window**.
- A **Selection** is rendered into one **Gist**; a **Gist** is published into one **Brief**.
- Every artifact (**Item**, **Selection**, **Run**) carries **Provenance**.
- A **KOL** maps informally to one or more **Sources** — never referenced from code.

## Example dialogue

> **Dev:** "When the YouTube **Source Adapter** finds a Karpathy video, does the **Item** record that he's a **KOL**?"
> **Architect:** "No. The **Item** records the channel as `author`. **KOL** is a curation concept that lives in `kols.yaml` and the prompt — adapters just read their per-source config and don't know about KOLs."
>
> **Dev:** "What if we couldn't get the transcript?"
> **Architect:** "The adapter still yields the **Item** with `payload_kind=metadata_only`. The renderer sees that and surfaces it as a one-line link without inventing takeaways."
>
> **Dev:** "If I re-run last week, do I get the same **Selection**?"
> **Architect:** "The **Items** in the **Corpus** are the same, yes. The **Selection** depends on the ranker and model version — both recorded in **Provenance**. Re-running with the same versions is deterministic; with different ones, it's the new behaviour."

## Flagged ambiguities

- "Source" was used to mean both the upstream system and the adapter that talks to it — resolved: the system is **Source**, the module is **Source Adapter**.
- "Item" used to also mean "thing in the brief" — resolved: that's a **Selection** entry now. **Items** are intrinsic; **Selections** are per-**Window**.
- "Brief" and "Gist" were swapped in some early notes — resolved: **Gist** is internal/long-form, **Brief** is public/bilingual.
- `topics_raw` (on **Item**, descriptive — what the source called it) vs `topics` (on **Selection** entry, prescriptive — `{Agent, Simulation}` per the prompt) — keep distinct.
