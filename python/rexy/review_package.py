"""Immutable, self-contained inputs for one offline review session."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from .corpus.items_store import ItemsStore
from .corpus.selections_store import SelectionsStore
from .domain import Window


def latest_git_review_package(packages_root: Path) -> Path:
    """Return the newest complete Review Package already synchronised by Git."""

    candidates: list[tuple[int, Path]] = []
    for manifest_path in packages_root.glob("*/*/manifest.json"):
        try:
            manifest = verify_review_package(manifest_path.parent)
            run_id = int(str(manifest["run_id"]))
        except (KeyError, TypeError, ValueError):
            continue
        candidates.append((run_id, manifest_path.parent))
    if not candidates:
        raise RuntimeError("no verified Review Package found in Git")
    return max(candidates, key=lambda candidate: candidate[0])[1]


def pull_git_review_updates() -> None:
    try:
        subprocess.run(
            ["git", "pull", "--ff-only"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git is required for `rexy review latest`") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"could not pull review packages from Git: {detail}") from exc


def build_review_package(
    *,
    corpus_root: Path,
    window: Window,
    gist_path: Path,
    brief_path: Path,
    output_root: Path,
    run_id: str,
    source_sha: str,
    generator_config_path: Path | None = None,
) -> Path:
    """Build the complete immutable review input for one successful run."""

    if output_root.exists():
        raise FileExistsError(f"review package already exists: {output_root}")

    entries = SelectionsStore(corpus_root / "selections").read(window)
    if not entries:
        raise FileNotFoundError(f"Selection missing for {window}")

    items_by_id = {
        item.id: item for item in ItemsStore(corpus_root / "items.jsonl").read_all()
    }
    selected_ids = [entry.item_id for entry in entries]
    missing_items = [item_id for item_id in selected_ids if item_id not in items_by_id]
    if missing_items:
        raise FileNotFoundError(
            f"review package missing selected Items: {', '.join(missing_items)}"
        )

    package_corpus = output_root / "corpus"
    ItemsStore(package_corpus / "items.jsonl").upsert_many(
        items_by_id[item_id] for item_id in selected_ids
    )
    SelectionsStore(package_corpus / "selections").write(window, entries)

    for item_id in selected_ids:
        payload_ref = items_by_id[item_id].payload_ref
        if payload_ref is None:
            continue
        source = corpus_root / "payloads" / payload_ref
        if not source.is_file():
            raise FileNotFoundError(
                f"review package payload missing for {item_id}: {payload_ref}"
            )
        target = package_corpus / "payloads" / payload_ref
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    matching_runs: list[Path] = []
    for source in sorted((corpus_root / "runs").glob("Run_*.json")):
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("window") == str(window):
            matching_runs.append(source)
    if not matching_runs:
        raise FileNotFoundError(f"review package provenance missing for {window}")
    for source in matching_runs:
        target = package_corpus / "runs" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    artifact_root = output_root / "Weekly_Gist"
    artifact_root.mkdir(parents=True, exist_ok=True)
    for source in (gist_path, brief_path):
        if not source.is_file():
            raise FileNotFoundError(f"review artifact missing: {source}")
        shutil.copy2(source, artifact_root / source.name)

    packaged_config: Path | None = None
    if generator_config_path is not None and generator_config_path.is_file():
        packaged_config = output_root / "config" / "generator.toml"
        packaged_config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(generator_config_path, packaged_config)

    files = {
        path.relative_to(output_root).as_posix(): _sha256(path)
        for path in sorted(output_root.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "source_sha": source_sha,
        "window": str(window),
        "artifacts": {
            "gist": (artifact_root / gist_path.name).relative_to(output_root).as_posix(),
            "brief": (artifact_root / brief_path.name).relative_to(output_root).as_posix(),
        },
        "generator_config": (
            packaged_config.relative_to(output_root).as_posix()
            if packaged_config is not None else None
        ),
        "files": files,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_root


def verify_review_package(package_root: Path) -> dict[str, object]:
    """Verify the complete package manifest and return its metadata."""

    manifest_path = package_root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("review package manifest missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"review package manifest invalid: {exc}") from exc
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported review package schema")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("review package manifest has no files")

    for relative, expected in files.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("review package manifest file entry invalid")
        path = package_root / relative
        try:
            path.resolve().relative_to(package_root.resolve())
        except ValueError as exc:
            raise ValueError(f"review package path escapes root: {relative}") from exc
        if not path.is_file():
            raise ValueError(f"review package file missing: {relative}")
        if _sha256(path) != expected:
            raise ValueError(f"review package checksum mismatch: {relative}")
    return manifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
