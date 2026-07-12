from __future__ import annotations

import hashlib
import json
import threading
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
import pytest

from rexy.weekly_review import WeeklyReviewSession
from rexy.weekly_review_ui import start_weekly_review_server
from rexy.corpus.items_store import ItemsStore
from rexy.corpus.selections_store import SelectionsStore
from rexy.domain import Item, PayloadKind, Scores, SelectionEntry, SourceType, Translations, Window
from rexy.generate.config import GeneratorConfig
from rexy.generate.llm.deep_note import MemoryDeepNoteWriter
from rexy.generate.review_ui import find_review_session


def test_finish_review_writes_edited_brief_to_knowledgecard_inbox(tmp_path: Path) -> None:
    package = tmp_path / ".rexy" / "reviews" / "29185698849"
    artifacts = package / "Weekly_Gist"
    artifacts.mkdir(parents=True)
    gist = artifacts / "Weekly_Gist_2026-07-12.md"
    brief = artifacts / "Weekly_Brief_2026-07-12.md"
    gist.write_text("reference gist", encoding="utf-8")
    brief.write_text("generated brief", encoding="utf-8")
    files = {
        path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (gist, brief)
    }
    (package / "manifest.json").write_text(
        json.dumps({
            "schema_version": 1,
            "run_id": "29185698849",
            "source_sha": "abc123",
            "window": "2026-07-05/2026-07-12",
            "artifacts": {
                "gist": "Weekly_Gist/Weekly_Gist_2026-07-12.md",
                "brief": "Weekly_Gist/Weekly_Brief_2026-07-12.md",
            },
            "files": files,
        }),
        encoding="utf-8",
    )
    inbox = tmp_path / "KnowledgeCard_Inbox"

    session = WeeklyReviewSession.open(package, inbox, tmp_path / ".rexy" / "reviews" / "29185698849")
    session.save_brief("reviewed brief")
    final = session.finish()

    assert session.gist_markdown == "reference gist"
    assert final == inbox / "weekly_brief_2026-07-12.md"
    assert final.read_text(encoding="utf-8") == "reviewed brief\n"
    assert brief.read_text(encoding="utf-8") == "generated brief"
    with pytest.raises(FileExistsError, match="reviewed weekly Brief already exists"):
        session.finish()


def test_offline_review_ui_serves_gist_and_edits_brief(tmp_path: Path) -> None:
    package = tmp_path / "package"
    artifacts = package / "Weekly_Gist"
    artifacts.mkdir(parents=True)
    gist = artifacts / "Weekly_Gist_2026-07-12.md"
    brief = artifacts / "Weekly_Brief_2026-07-12.md"
    gist.write_text("reference gist", encoding="utf-8")
    brief.write_text("generated brief", encoding="utf-8")
    files = {
        path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (gist, brief)
    }
    (package / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "run_id": "29185698849",
        "source_sha": "abc123",
        "window": "2026-07-05/2026-07-12",
        "artifacts": {
            "gist": "Weekly_Gist/Weekly_Gist_2026-07-12.md",
            "brief": "Weekly_Gist/Weekly_Brief_2026-07-12.md",
        },
        "files": files,
    }), encoding="utf-8")
    inbox = tmp_path / "KnowledgeCard_Inbox"
    session = WeeklyReviewSession.open(package, inbox, tmp_path / "workspace")
    server, url = start_weekly_review_server(session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        page = urllib.request.urlopen(url, timeout=2).read().decode()
        assert "Weekly Review" in page
        assert "reference gist" in page
        assert "generated brief" in page
        assert "Discard Brief" in page
        assert "No eligible DeepNote candidates." in page
        assert "Generate selected DeepNotes" not in page
        assert "position:fixed" in page
        assert "catch(error)" in page

        token = url.split("token=", 1)[1]
        save = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/save?token={token}",
            data=json.dumps({"markdown": "reviewed brief"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(save, timeout=2).read()
        discard = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/discard?token={token}",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        discard_result = json.loads(urllib.request.urlopen(discard, timeout=2).read())
        assert discard_result == {"discarded": True}
        assert not (tmp_path / "workspace" / "work" / "edited_weekly_brief.md").exists()
        assert session.brief_discarded
        finish = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/finish?token={token}",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(finish, timeout=2).read()
        assert exc_info.value.code == 400
        assert not (inbox / "weekly_brief_2026-07-12.md").exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_deep_notes_use_only_packaged_selection_and_evidence(tmp_path: Path) -> None:
    package = tmp_path / "package"
    corpus = package / "corpus"
    window = Window.parse("2026-07-05/2026-07-12")
    payload_ref = "selected.txt"
    (corpus / "payloads").mkdir(parents=True)
    (corpus / "payloads" / payload_ref).write_text("source evidence", encoding="utf-8")
    item = Item(
        id="arxiv:selected",
        source_type=SourceType.ARXIV,
        source_native_id="selected",
        canonical_url="https://example.com/selected",
        title="Simulation world model",
        author="Author",
        published_at=date(2026, 7, 10),
        type="paper",
        topics_raw=[],
        payload_kind=PayloadKind.EXTRACT,
        payload_ref=payload_ref,
        fetched_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        adapter="test",
    )
    entry = SelectionEntry(
        item_id=item.id,
        window=window,
        rank=1,
        scores=Scores(4.8, 4.8, 4.8, 4.8),
        tldr_en="Simulation evidence",
        takeaways_en=["A", "B", "C"],
        implication_en="Connects agent and simulation",
        topics=["Agent", "Simulation"],
        translations=Translations(),
        model="test",
        prompt_version="v1",
        generated_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
    )
    ItemsStore(corpus / "items.jsonl").upsert_many([item])
    SelectionsStore(corpus / "selections").write(window, [entry])
    artifacts = package / "Weekly_Gist"
    artifacts.mkdir()
    gist = artifacts / "Weekly_Gist_2026-07-12.md"
    brief = artifacts / "Weekly_Brief_2026-07-12.md"
    gist.write_text("gist", encoding="utf-8")
    brief.write_text("brief", encoding="utf-8")
    package_files = [path for path in package.rglob("*") if path.is_file()]
    files = {
        path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in package_files
    }
    (package / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "run_id": "29185698849",
        "source_sha": "abc123",
        "window": str(window),
        "artifacts": {
            "gist": gist.relative_to(package).as_posix(),
            "brief": brief.relative_to(package).as_posix(),
        },
        "files": files,
    }), encoding="utf-8")
    workspace = tmp_path / ".rexy" / "reviews" / "29185698849"
    session = WeeklyReviewSession.open(package, tmp_path / "KnowledgeCard_Inbox", workspace)

    candidates = session.deep_note_candidates(GeneratorConfig())
    drafts = session.generate_deep_notes(
        ["arxiv:selected"], GeneratorConfig(), MemoryDeepNoteWriter()
    )

    assert [candidate.entry.item_id for candidate in candidates] == ["arxiv:selected"]
    assert len(drafts) == 1
    assert drafts[0].is_relative_to(workspace)
    assert "memory stub" in drafts[0].read_text(encoding="utf-8")
    assert not (package / "corpus" / "deep_notes").exists()
    assert not (package / "work").exists()
    with pytest.raises(ValueError, match="DeepNote review incomplete"):
        session.finish()
    find_review_session(
        workspace / "corpus",
        session.inbox_root,
        window.end.isoformat(),
        "arxiv:selected",
    ).publish()
    assert session.finish().is_file()

    server, url = start_weekly_review_server(
        session,
        config=GeneratorConfig(),
        writer_factory=lambda: MemoryDeepNoteWriter(),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        page = urllib.request.urlopen(url, timeout=2).read().decode()
        assert "Simulation world model" in page
        assert "Generate selected DeepNotes" in page
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
