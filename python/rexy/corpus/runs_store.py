"""Per-run provenance files (ADR-0005).

One JSON file per ingestion or generation run. Atomic write so a partial
run never produces a half-written record.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..domain import Window, now_utc


@dataclass(slots=True)
class AdapterRunStat:
    name: str
    config_sha: str
    items_yielded: int = 0
    items_new: int = 0
    items_updated: int = 0
    duration_s: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IngestionRun:
    run_id: str
    window: Window
    started_at: datetime
    finished_at: datetime | None = None
    adapters: list[AdapterRunStat] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "kind": "ingestion",
            "run_id": self.run_id,
            "window": str(self.window),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at) if self.finished_at else None,
            "adapters": [asdict(a) for a in self.adapters],
        }


def make_run_id(when: datetime | None = None) -> str:
    when = when or now_utc()
    return when.strftime("%Y%m%dT%H%M%SZ")


class RunsStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, run: IngestionRun) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"Run_{run.run_id}.json"
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.root,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            json.dump(run.to_jsonable(), tmp, indent=2, ensure_ascii=False)
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
        return path

    def latest_window(self) -> Window | None:
        """Return the most recent ingestion run's Window, or None."""

        if not self.root.exists():
            return None
        latest: tuple[str, Window] | None = None
        for path in self.root.glob("Run_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if data.get("kind") != "ingestion":
                continue
            run_id = data.get("run_id")
            window_str = data.get("window")
            if not run_id or not window_str:
                continue
            try:
                window = Window.parse(window_str)
            except ValueError:
                continue
            if latest is None or run_id > latest[0]:
                latest = (run_id, window)
        return latest[1] if latest else None


def _iso(dt: datetime) -> str:
    from datetime import timezone

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
