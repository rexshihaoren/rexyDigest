"""Selection JSONL store under `corpus/selections/`.

One file per **Selection**: `Selection_<end-date>.jsonl`. Each line is one
**SelectionEntry** in rank order. Atomic write via temp + replace.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Iterable

from ..domain import SelectionEntry, Window


class SelectionsStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path_for(self, window: Window) -> Path:
        return self.root / f"Selection_{window.end.isoformat()}.jsonl"

    def write(self, window: Window, entries: Iterable[SelectionEntry]) -> Path:
        """Atomically write one Selection file in the order entries are given."""
        target = self._path_for(window)
        self.root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.root,
            prefix=target.name + ".",
            suffix=".tmp",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            for entry in entries:
                tmp.write(json.dumps(entry.to_jsonable(), ensure_ascii=False))
                tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(target)
        return target

    def read(self, window: Window) -> list[SelectionEntry]:
        path = self._path_for(window)
        if not path.exists():
            return []
        out: list[SelectionEntry] = []
        with path.open("r", encoding="utf-8") as fp:
            for line_no, raw in enumerate(fp, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    out.append(SelectionEntry.from_jsonable(json.loads(raw)))
                except (KeyError, ValueError) as exc:
                    raise ValueError(
                        f"{path}:{line_no}: malformed SelectionEntry: {exc}"
                    ) from exc
        return out
