"""Adapter registry: reads `config/sources/*.toml` and instantiates adapters.

Convention: each `.toml` file is one configured adapter instance. The
filename stem is the default adapter name. Two reserved top-level keys:

  source_type = "arxiv" | "rss" | ...   (required)
  disabled    = true | false            (optional; default false)

Everything else in the file is forwarded verbatim as `config` to the adapter
constructor. SHA-1 of the raw TOML bytes is recorded as `config_sha` in the
run's provenance file so a config change is detectable from a Run alone.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import SourceAdapter, build_adapter


@dataclass(slots=True, frozen=True)
class ConfiguredAdapter:
    name: str
    source_type: str
    config_sha: str
    adapter: SourceAdapter


def load_adapters(config_dir: Path) -> list[ConfiguredAdapter]:
    """Load and instantiate every enabled adapter under `config_dir`.

    Adapters are returned in filename-sorted order so runs are deterministic.
    """

    configured: list[ConfiguredAdapter] = []
    if not config_dir.exists():
        return configured

    for toml_path in sorted(config_dir.glob("*.toml")):
        raw = toml_path.read_bytes()
        try:
            data = tomllib.loads(raw.decode("utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"{toml_path}: invalid TOML: {exc}") from exc

        if data.pop("disabled", False):
            continue

        source_type = data.pop("source_type", None)
        if not source_type:
            raise ValueError(f"{toml_path}: missing `source_type` top-level key")

        name = data.pop("name", None) or toml_path.stem
        adapter = build_adapter(name=name, source_type=source_type, config=data)
        configured.append(
            ConfiguredAdapter(
                name=name,
                source_type=source_type,
                config_sha=hashlib.sha1(raw).hexdigest()[:16],
                adapter=adapter,
            )
        )
    return configured
