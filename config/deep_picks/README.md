# Manual deep-note picks

One TOML file per **window end** (same date as `Selection_<end>.jsonl`):

`YYYY-MM-DD.toml`

```toml
# 0–2 item_ids from that week’s Selection (see gist or corpus/selections/)
item_ids = [
  "rss:https___example.com_post",
]
```

Then:

```bash
PYTHONPATH=python .venv/bin/python -m rexy deep-notes --end YYYY-MM-DD --llm memory
```

Writes `KnowledgeCard_Inbox/deep_<id>_<end>.md` (default inbox path).
