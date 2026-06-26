"""Ingestion orchestrator.

Tied together by the CLI but separable so it can be exercised in tests
with an InMemoryAdapter and a tmp_path corpus.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from .corpus.items_store import ItemsStore
from .corpus.payloads_store import PayloadsStore
from .corpus.runs_store import (
    AdapterRunStat,
    IngestionRun,
    RunsStore,
    make_run_id,
)
from .domain import Item, PayloadKind, Window, now_utc
from .sources._registry import ConfiguredAdapter
from .sources import AdapterError


def run_ingestion(
    adapters: Iterable[ConfiguredAdapter],
    window: Window,
    corpus_root: Path,
) -> IngestionRun:
    """Drive every adapter through `window`, persist into the corpus, return the Run."""

    items_store = ItemsStore(corpus_root / "items.jsonl")
    payloads_store = PayloadsStore(corpus_root / "payloads")
    runs_store = RunsStore(corpus_root / "runs")

    run = IngestionRun(
        run_id=make_run_id(),
        window=window,
        started_at=now_utc(),
    )

    for configured in adapters:
        stat = AdapterRunStat(name=configured.name, config_sha=configured.config_sha)
        run.adapters.append(stat)
        t0 = time.monotonic()
        items_for_upsert: list[Item] = []
        try:
            for fetched in configured.adapter.fetch(window):
                # Item-time invariant: adapter must filter by published_at in window.
                if not window.contains(fetched.item.published_at):
                    stat.errors.append(
                        f"adapter yielded out-of-window item {fetched.item.id} "
                        f"(published_at={fetched.item.published_at})"
                    )
                    continue

                payload = fetched.payload
                kind = fetched.item.payload_kind
                if kind in (PayloadKind.EXTRACT, PayloadKind.FULL_TEXT):
                    if payload is None:
                        stat.errors.append(
                            f"item {fetched.item.id} declared kind={kind} but no payload"
                        )
                        continue
                    payload_ref = payloads_store.write(
                        item_id=fetched.item.id,
                        payload=payload,
                        suffix=fetched.payload_suffix,
                    )
                    fetched.item.payload_ref = payload_ref
                else:
                    fetched.item.payload_ref = None

                items_for_upsert.append(fetched.item)
                stat.items_yielded += 1
        except AdapterError as exc:
            stat.errors.append(f"AdapterError: {exc}")
        except Exception as exc:  # pragma: no cover - defensive against rogue adapters
            stat.errors.append(f"{type(exc).__name__}: {exc}")
        finally:
            stat.duration_s = round(time.monotonic() - t0, 3)

        if items_for_upsert:
            added, updated = items_store.upsert_many(items_for_upsert)
            stat.items_new = added
            stat.items_updated = updated

    run.finished_at = now_utc()
    runs_store.write(run)
    return run
