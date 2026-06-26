# Window owned by ingestion

The **Window** is decided at the ingestion CLI invocation (default: last 7 days from `now`; override via `--window` or the existing `END_DATE` env var). Every **Source Adapter** filters its fetch results to Items whose `published_at` falls inside the Window — adapters do not yield out-of-Window Items. The Generator's default Window is the latest ingestion run's Window (read from `corpus/runs/Run_<id>.json`); the Publisher reads its Window from the **Selection** file's `window` field, never from the filename.

## Why this option, not "Window owned by Generator"

Editorial intent: a weekly **Brief** must contain content published in *that week*. Letting ingestion be unbounded ("fetch everything new since last run") would mean a brief published on Friday could include something published a month ago that an adapter only just discovered — drift the editor would have to correct manually. Filtering at ingestion makes this a hard pipeline guarantee instead of a soft hope.

## Consequences

- The **Corpus** still accumulates across runs — Items are not deleted between weeks. Re-running last week's generator is just `--window 2026-04-26/2026-05-03`; the Corpus retains older Items with their `published_at`.
- A "missed week" requires an explicit catch-up ingestion run with that week's Window — there is no automatic backfill from `since last run`.
- The "filename is the source of truth for the date" anti-pattern in the current Node publisher dies: `Weekly_Gist_<end>.md` is a *display* convention, the truth is the Selection's `window` field.
