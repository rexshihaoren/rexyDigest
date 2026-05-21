# Manual deep-note picks

One TOML file per **window end** (same date as `Selection_<end>.jsonl`):

`YYYY-MM-DD.toml`

Pick `0-2` IDs from the internal gist's `Top Items for Rex Ren` table:

`Weekly_Gist/Weekly_Gist_<end>.md`

That table exposes an `ItemID` column for this purpose. The public brief does
not include IDs.

```toml
# 0–2 item_ids from that week’s internal Weekly_Gist table.
item_ids = [
  "rss:https___example.com_post",
]
```

Then:

```bash
PYTHONPATH=python .venv/bin/python -m rexy deep-notes --end YYYY-MM-DD --llm memory
```

Writes `KnowledgeCard_Inbox/deep_<id>_<end>.md` (default inbox path).
