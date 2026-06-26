"""Append-and-upsert store for `items.jsonl`.

Items are upserted by `id` — re-fetching the same Item overwrites the prior
record (last-write-wins). The whole file is rewritten on commit; this is fine
at the corpus sizes we expect (thousands of Items, not millions).
"""

from __future__ import annotations

import json
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

from ..domain import Item


class ItemsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read_all(self) -> list[Item]:
        if not self.path.exists():
            return []
        items: list[Item] = []
        with self.path.open("r", encoding="utf-8") as fp:
            for line_no, raw in enumerate(fp, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    items.append(Item.from_jsonable(json.loads(raw)))
                except (KeyError, ValueError) as exc:
                    raise ValueError(
                        f"{self.path}:{line_no}: malformed Item record: {exc}"
                    ) from exc
        return items

    def upsert_many(self, new_items: Iterable[Item]) -> tuple[int, int]:
        """Merge `new_items` into the store. Returns (added, updated).

        Each Item is validated for persistence (payload_kind / payload_ref
        consistency) before being written.
        """

        existing = OrderedDict((it.id, it) for it in self.read_all())
        added = 0
        updated = 0
        for it in new_items:
            it.validate_for_persistence()
            if it.id in existing:
                updated += 1
            else:
                added += 1
            existing[it.id] = it
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic-ish write: temp file in same dir, then replace.
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.path.parent,
            prefix=self.path.name + ".",
            suffix=".tmp",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            for it in existing.values():
                tmp.write(json.dumps(it.to_jsonable(), ensure_ascii=False))
                tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(self.path)
        return added, updated
