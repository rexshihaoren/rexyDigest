from __future__ import annotations

import json
import shutil
import stat
from datetime import date, datetime, timezone
from pathlib import Path

from rexy.corpus.items_store import ItemsStore
from rexy.corpus.selections_store import SelectionsStore
from rexy.domain import (
    Item,
    PayloadKind,
    Scores,
    SelectionEntry,
    SourceType,
    Translations,
    Window,
)
from rexy.review_package import (
    build_review_package,
    verify_review_package,
)
from rexy.cli import main


WINDOW = Window.parse("2026-07-05/2026-07-12")


def _item(item_id: str, payload_ref: str | None) -> Item:
    return Item(
        id=item_id,
        source_type=SourceType.ARXIV,
        source_native_id=item_id.split(":", 1)[1],
        canonical_url=f"https://example.com/{item_id}",
        title=f"Title {item_id}",
        author="Author",
        published_at=date(2026, 7, 10),
        type="paper",
        topics_raw=[],
        payload_kind=PayloadKind.EXTRACT if payload_ref else PayloadKind.METADATA_ONLY,
        payload_ref=payload_ref,
        fetched_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        adapter="test",
    )


def _entry(item_id: str, rank: int) -> SelectionEntry:
    return SelectionEntry(
        item_id=item_id,
        window=WINDOW,
        rank=rank,
        scores=Scores(4.5, 4.5, 4.5, 4.5),
        tldr_en="Summary",
        takeaways_en=["A", "B", "C"],
        implication_en="Implication",
        topics=["Agent", "Simulation"],
        translations=Translations(),
        model="test",
        prompt_version="v1",
        generated_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
    )


def test_build_review_package_contains_exact_run_inputs(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    (corpus / "payloads").mkdir(parents=True)
    (corpus / "payloads" / "selected.txt").write_text("selected evidence", encoding="utf-8")
    (corpus / "payloads" / "unselected.txt").write_text("unselected evidence", encoding="utf-8")
    ItemsStore(corpus / "items.jsonl").upsert_many([
        _item("arxiv:selected", "selected.txt"),
        _item("arxiv:metadata", None),
        _item("arxiv:unselected", "unselected.txt"),
    ])
    SelectionsStore(corpus / "selections").write(
        WINDOW,
        [_entry("arxiv:selected", 1), _entry("arxiv:metadata", 2)],
    )
    (corpus / "runs").mkdir()
    (corpus / "runs" / "Run_current.json").write_text(
        json.dumps({"kind": "generation", "run_id": "current", "window": str(WINDOW)}),
        encoding="utf-8",
    )
    (corpus / "runs" / "Run_old.json").write_text(
        json.dumps({"kind": "generation", "run_id": "old", "window": "2026-06-21/2026-06-28"}),
        encoding="utf-8",
    )
    gist = tmp_path / "Weekly_Gist_2026-07-12.md"
    brief = tmp_path / "Weekly_Brief_2026-07-12.md"
    gist.write_text("gist", encoding="utf-8")
    brief.write_text("brief", encoding="utf-8")
    generator_config = tmp_path / "generator.toml"
    generator_config.write_text('gemini_model = "test-model"\n', encoding="utf-8")

    package = build_review_package(
        corpus_root=corpus,
        window=WINDOW,
        gist_path=gist,
        brief_path=brief,
        output_root=tmp_path / "package",
        run_id="29185698849",
        source_sha="abc123",
        generator_config_path=generator_config,
    )

    packaged_items = ItemsStore(package / "corpus" / "items.jsonl").read_all()
    assert {item.id for item in packaged_items} == {"arxiv:selected", "arxiv:metadata"}
    assert (package / "corpus" / "payloads" / "selected.txt").read_text() == "selected evidence"
    assert not (package / "corpus" / "payloads" / "unselected.txt").exists()
    assert (package / "Weekly_Gist" / gist.name).read_text() == "gist"
    assert (package / "Weekly_Gist" / brief.name).read_text() == "brief"
    assert (package / "corpus" / "runs" / "Run_current.json").is_file()
    assert (package / "config" / "generator.toml").read_text() == 'gemini_model = "test-model"\n'
    assert not (package / "corpus" / "runs" / "Run_old.json").exists()
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "29185698849"
    assert manifest["source_sha"] == "abc123"
    assert manifest["window"] == str(WINDOW)
    assert set(manifest["files"]) == {
        "Weekly_Gist/Weekly_Brief_2026-07-12.md",
        "Weekly_Gist/Weekly_Gist_2026-07-12.md",
        "corpus/items.jsonl",
        "corpus/payloads/selected.txt",
        "corpus/runs/Run_current.json",
        "corpus/selections/Selection_2026-07-12.jsonl",
        "config/generator.toml",
    }


def test_verify_review_package_rejects_tampered_evidence(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    evidence = package / "evidence.txt"
    evidence.write_text("original", encoding="utf-8")
    import hashlib

    manifest = {
        "schema_version": 1,
        "run_id": "29185698849",
        "source_sha": "abc123",
        "window": str(WINDOW),
        "files": {"evidence.txt": hashlib.sha256(b"original").hexdigest()},
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    evidence.write_text("tampered", encoding="utf-8")

    try:
        verify_review_package(package)
    except ValueError as exc:
        assert "checksum mismatch: evidence.txt" in str(exc)
    else:
        raise AssertionError("tampered package was accepted")


def test_review_latest_cli_pulls_and_uses_latest_git_review_package(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    package = tmp_path / "Weekly_Gist" / "Review_Packages" / "2026-07-12" / "29185698849"
    package.mkdir(parents=True)
    evidence = package / "evidence.txt"
    evidence.write_text("evidence", encoding="utf-8")
    import hashlib

    (package / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "29185698849",
                "source_sha": "abc123",
                "window": str(WINDOW),
                "files": {"evidence.txt": hashlib.sha256(b"evidence").hexdigest()},
            }
        ),
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git = bin_dir / "git"
    git.write_text(
        "#!/bin/sh\n"
        "exit 0\n",
        encoding="utf-8",
    )
    git.chmod(git.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
    monkeypatch.chdir(tmp_path)

    result = main(["review", "latest", "--no-open"])

    assert result == 0
    assert (package / "evidence.txt").read_text() == "evidence"
    assert f"review_package={package}" in capsys.readouterr().out
