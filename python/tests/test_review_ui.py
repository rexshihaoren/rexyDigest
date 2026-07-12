"""Minimal DeepNote review UI state and publication behavior."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

import pytest

from rexy.generate.llm.deep_note import MemoryDeepNoteWriter
from rexy.generate.review_ui import ReviewSession, find_review_session, start_review_server


def _workspace(tmp_path: Path) -> tuple[Path, Path, Path]:
    draft = tmp_path / "draft.md"
    draft.write_text(MemoryDeepNoteWriter().write(
        item_id="youtube:x",
        item_type="video",
        source="YouTube",
        title="Example",
        author="A",
        url="https://youtube.com/watch?v=abc12345678",
        payload="evidence",
    ), encoding="utf-8")
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"jpeg")
    sidecar = tmp_path / "visuals.json"
    sidecar.write_text(json.dumps({
        "schema_version": 1,
        "complete": True,
        "candidates": [{
            "candidate_id": "c1",
            "section_heading": "### 03｜与 AI X Simulation 的关系",
            "asset_path": str(image),
            "alt": "候选图",
            "reason": "Shows evidence.",
            "signals": {"judge_decision": "use", "judge_confidence": "high"},
            "approval": {"status": "pending", "reviewed_at": None},
        }],
    }), encoding="utf-8")
    return draft, sidecar, tmp_path / "final.md"


def test_review_requires_terminal_visual_decision_before_publish(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    session = ReviewSession(draft, sidecar, final)

    assert session.state()["publish_ready"] is False
    with pytest.raises(ValueError, match="visual review incomplete"):
        session.publish()

    session.approve("c1")
    assert session.state()["publish_ready"] is True
    session.publish()

    assert "![候选图]" in final.read_text(encoding="utf-8")
    assert "![候选图]" not in draft.read_text(encoding="utf-8")


def test_preview_markdown_tracks_the_current_visual_decision(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    session = ReviewSession(draft, sidecar, final)

    assert "![候选图]" not in session.state()["preview_markdown"]

    session.approve("c1")
    assert "![候选图]" in session.state()["preview_markdown"]

    session.choose_no_visual("### 03｜与 AI X Simulation 的关系")
    assert "![候选图]" not in session.state()["preview_markdown"]


def test_text_edit_invalidates_only_changed_section_and_can_close(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    session = ReviewSession(draft, sidecar, final)
    session.approve("c1")
    changed = draft.read_text(encoding="utf-8").replace(
        "- 重要性：两者接上后，agent 能在行动前先校准对世界的理解。",
        "- 重要性：真实商店让 agent 面对物理库存和人类行为。",
    )

    result = session.save_markdown(changed)

    assert result["changed_sections"] == ["### 03｜与 AI X Simulation 的关系"]
    assert session.state()["candidates"][0]["approval"]["status"] == "stale"
    assert session.state()["publish_ready"] is False
    assert final.exists() is False


def test_no_visual_is_terminal_and_invalid_markdown_cannot_save(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    session = ReviewSession(draft, sidecar, final)
    session.choose_no_visual("### 03｜与 AI X Simulation 的关系")
    assert session.state()["publish_ready"] is True

    with pytest.raises(ValueError, match="invalid deep note Markdown"):
        session.save_markdown("# broken")


def test_local_http_ui_serves_review_and_persists_approval(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    session = ReviewSession(draft, sidecar, final)
    server, url = start_review_server(session)
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        page = urllib.request.urlopen(url, timeout=2).read().decode()
        assert "DeepNote Review" in page
        assert "Finish review" in page

        token = url.split("token=", 1)[1]
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/approve?token={token}",
            data=json.dumps({"candidate_id": "c1"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        state = json.loads(urllib.request.urlopen(request, timeout=2).read())
        assert state["publish_ready"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_local_http_ui_serves_executable_javascript(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required to syntax-check the browser script")
    draft, sidecar, final = _workspace(tmp_path)
    server, url = start_review_server(ReviewSession(draft, sidecar, final))
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        page = urllib.request.urlopen(url, timeout=2).read().decode()
        script = re.search(r"<script>(.*?)</script>", page, re.DOTALL)
        assert script is not None

        result = subprocess.run(
            [node, "--check"],
            input=script.group(1),
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_local_http_ui_explains_visual_choices_and_offers_preview(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    server, url = start_review_server(ReviewSession(draft, sidecar, final))
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        page = urllib.request.urlopen(url, timeout=2).read().decode()

        assert "Use this visual" in page
        assert "Publish this section without a visual" in page
        assert "Preview note" in page
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_local_http_ui_opens_on_the_decision_applied_preview(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    server, url = start_review_server(ReviewSession(draft, sidecar, final))
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        page = urllib.request.urlopen(url, timeout=2).read().decode()

        assert 'id="preview-tab" role="tab" aria-selected="true"' in page
        assert 'id="edit-tab" role="tab" aria-selected="false"' in page
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_published_markdown_remains_clickable_from_review_server(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    server, url = start_review_server(ReviewSession(draft, sidecar, final))
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    token = url.split("token=", 1)[1]

    def post(path: str, payload: dict[str, str]) -> dict:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}{path}?token={token}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return json.loads(urllib.request.urlopen(request, timeout=2).read())

    try:
        post("/api/approve", {"candidate_id": "c1"})
        published = post("/api/publish", {})
        rendered = urllib.request.urlopen(
            f"http://127.0.0.1:{server.server_port}{published['final_url']}",
            timeout=2,
        ).read().decode()

        assert "![候选图]" in rendered
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_legacy_final_is_staged_as_image_free_editable_markdown(tmp_path: Path) -> None:
    draft, sidecar, _final = _workspace(tmp_path)
    sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
    sidecar_data["candidates"][0]["approval"] = {
        "status": "approved",
        "reviewed_at": "2026-06-10T00:00:00Z",
    }
    corpus = tmp_path / "corpus"
    stored = corpus / "visuals" / "youtube_x" / "2026-06-10" / "candidates.json"
    stored.parent.mkdir(parents=True)
    stored.write_text(json.dumps(sidecar_data), encoding="utf-8")
    inbox = tmp_path / "KnowledgeCard_Inbox"
    inbox.mkdir()
    final = inbox / "deep_youtube_x_2026-06-10.md"
    final.write_text(
        draft.read_text(encoding="utf-8")
        + f"\n![候选图]({sidecar_data['candidates'][0]['asset_path']})\n",
        encoding="utf-8",
    )

    session = find_review_session(corpus, inbox, "2026-06-10", "youtube:x")
    state = session.state()

    assert session.draft_path == corpus / "deep_notes" / "youtube_x" / "2026-06-10" / "draft.md"
    assert session.sidecar_path == stored
    assert "![候选图]" not in state["markdown"]
    assert "![候选图]" in state["preview_markdown"]


def test_incomplete_enrichment_requires_explicit_text_only_waiver(tmp_path: Path) -> None:
    draft, sidecar, final = _workspace(tmp_path)
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["complete"] = False
    data["error"] = "Gemini unavailable"
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    session = ReviewSession(draft, sidecar, final)

    assert session.state()["publish_ready"] is False
    session.waive_incomplete()
    assert session.state()["publish_ready"] is True
