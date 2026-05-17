# Source Adapter port; minimum two adapters before introducing it

Five **Source** families (RSS, YouTube, arXiv, podcasts, blogs) have radically different fetch and parse semantics, but they all need to produce the same **Item** shape into the **Corpus**. We introduce a `SourceAdapter` Protocol (Python) with the contract `fetch(window: Window) -> Iterator[FetchedItem]`, where `FetchedItem` carries the fully-normalised Item plus an optional payload byte string. The framework owns persistence; adapters are pure and testable in-memory. Each adapter is self-configuring via `config/sources/<name>.toml` — there is no uniform "Query" type across adapters because different sources don't have queries in common.

The port is only justified when at least **two** real adapters exist (per [DEEPENING.md](../ai/skills/improve-codebase-architecture/DEEPENING.md)'s "one adapter = hypothetical seam, two = real"). Phase 1 ships with **`ArxivAdapter` + `RssAdapter`** as the inaugural pair — both have stable APIs, no auth, and abstracts/descriptions land cleanly in `payload_kind=extract`.

## Considered options

- **Uniform `fetch(queries, window)` across adapters** — rejected: would force a union-type "Query" that lies about what each source actually accepts.
- **Adapter writes payloads to disk directly** — rejected: couples adapters to filesystem layout and makes them harder to test.
- **Generate per-source configs from a master `kols.yaml`** — deferred: do it manually first; only build a generator if the manual cross-reference stops paying.

## Update: YouTube adapter shipped

`YoutubeAdapter` ([python/rexy/sources/youtube_adapter.py](../../python/rexy/sources/youtube_adapter.py)) ingests channel videos via YouTube's public Atom feed (`https://www.youtube.com/feeds/videos.xml?channel_id=…`) reusing the RSS adapter's `parse_feed_document` hook for testability. Transcripts are best-effort through `youtube-transcript-api`; on failure or absence the adapter falls back to the video description (`payload_kind=extract`) or `metadata_only`, **never** an `AdapterError`. Per-channel `kol = "<slug>"` config injects a `kol:<slug>` marker into `Item.topics_raw` so the generator's pre-filter and pre-rank stages can favour KOL-listed sources without touching adapter code.

## Deferred (intentionally)

- **Cross-source-type dedup** — a Latent Space episode appearing as both a YouTube video and a podcast RSS entry sits in the **Corpus** as two distinct **Items**. Add a `merged_into` field later without breaking the schema.
- **Concurrency, rate limiting, retries** — framework-level concerns, not part of the port.
