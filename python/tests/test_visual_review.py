"""Image judge and human approval form one durable DeepNote workflow."""

from __future__ import annotations

import json
from pathlib import Path

from rexy.generate.llm.deep_note import MemoryDeepNoteWriter
from rexy.generate.visual_review import JudgeResult, approve_and_render, judge_candidates


class _Judge:
    model = "fixture-vision"

    def judge(self, *, section_text: str, image_path: Path, reason: str) -> JudgeResult:
        assert section_text
        assert image_path.exists()
        return JudgeResult("use", "high", f"supports section: {reason}")


class _ComparativeJudge(_Judge):
    model = "fixture-comparative-vision"

    def __init__(self) -> None:
        self.calls = 0

    def judge_section(self, *, section_text: str, candidates: list[dict]) -> dict[str, JudgeResult]:
        self.calls += 1
        assert len(candidates) == 1
        return {candidates[0]["candidate_id"]: JudgeResult("use", "high", "best of set")}


def test_judge_then_approve_inserts_images_once_and_persists_review(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text(MemoryDeepNoteWriter().write(
        item_id="youtube:x",
        item_type="video",
        source="YouTube",
        title="Example",
        author="A",
        url="https://youtube.com/watch?v=abc12345678",
        payload="timed evidence",
    ), encoding="utf-8")
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"jpeg fixture")
    sidecar = tmp_path / "candidates.json"
    sidecar.write_text(json.dumps({
        "schema_version": 1,
        "candidates": [{
            "candidate_id": "c1",
            "section_heading": "### 03｜与 AI X Simulation 的关系",
            "asset_path": str(image),
            "alt": "真实世界商店",
            "reason": "Shows physical deployment.",
            "signals": {},
            "approval": {"status": "pending", "reviewed_at": None},
        }],
    }), encoding="utf-8")

    judge_candidates(note, sidecar, _Judge())
    approve_and_render(note, sidecar, ["c1"])
    approve_and_render(note, sidecar, ["c1"])

    markdown = note.read_text(encoding="utf-8")
    assert markdown.count(f"![真实世界商店]({image})") == 1
    saved = json.loads(sidecar.read_text(encoding="utf-8"))
    assert saved["candidates"][0]["signals"]["judge_model"] == "fixture-vision"
    assert saved["candidates"][0]["signals"]["judge_decision"] == "use"
    assert saved["candidates"][0]["approval"]["status"] == "approved"
    assert saved["candidates"][0]["approval"]["reviewed_at"]


def test_comparative_judge_runs_once_per_section(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text(MemoryDeepNoteWriter().write(
        item_id="youtube:x", item_type="video", source="YouTube", title="Example",
        author="A", url="https://youtube.com/watch?v=abc12345678", payload="evidence",
    ), encoding="utf-8")
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"jpeg")
    sidecar = tmp_path / "candidates.json"
    sidecar.write_text(json.dumps({"candidates": [{
        "candidate_id": "c1",
        "section_heading": "### 03｜与 AI X Simulation 的关系",
        "asset_path": str(image),
        "reason": "Shows evidence.",
        "signals": {},
        "approval": {"status": "pending", "reviewed_at": None},
    }]}), encoding="utf-8")
    judge = _ComparativeJudge()

    judge_candidates(note, sidecar, judge)

    assert judge.calls == 1
    saved = json.loads(sidecar.read_text(encoding="utf-8"))
    assert saved["candidates"][0]["signals"]["judge_reason"] == "best of set"
