"""Image-aware judging and durable human approval for DeepNote visuals."""

from __future__ import annotations

import json
import mimetypes
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from .deep_note_visuals import VisualReview, render_approved_visuals
from .llm.gemini_common import resolve_gemini_api_key, user_facing_gemini_error


JudgeDecision = Literal["use", "weak", "reject"]
JudgeConfidence = Literal["high", "medium", "low"]


@dataclass(frozen=True, slots=True)
class JudgeResult:
    decision: JudgeDecision
    confidence: JudgeConfidence
    reason: str


class VisualJudge(Protocol):
    model: str

    def judge(self, *, section_text: str, image_path: Path, reason: str) -> JudgeResult: ...


class GeminiVisualJudge:
    """Semantic section-to-image judge. It ranks; it never approves."""

    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None) -> None:
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("google-genai not installed") from exc
        key = resolve_gemini_api_key(api_key)
        if not key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY required for visual judging")
        self._client = genai.Client(api_key=key)
        self._types = genai_types
        self.model = model

    def judge(self, *, section_text: str, image_path: Path, reason: str) -> JudgeResult:
        prompt = f"""Judge whether this source-bound image materially improves the DeepNote section.

Prefer diagrams, charts, demonstrations, code, UI, whiteboards, and direct evidence.
Reject talking heads, logos, title cards, decoration, and redundant text.
No visual is valid. Do not approve; only rank relevance.

Section:
{section_text[:6000]}

Candidate rationale:
{reason}

Return JSON only:
{{"decision":"use|weak|reject","confidence":"high|medium|low","reason":"short explanation"}}
"""
        mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        part = self._types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt, part],
                config=self._types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            raw = json.loads((response.text or "{}").strip())
            decision = str(raw.get("decision", "reject")).lower()
            confidence = str(raw.get("confidence", "low")).lower()
            if decision not in {"use", "weak", "reject"}:
                decision = "reject"
            if confidence not in {"high", "medium", "low"}:
                confidence = "low"
            return JudgeResult(decision, confidence, str(raw.get("reason", ""))[:500])  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - live provider boundary
            raise RuntimeError(f"Gemini visual judge failed: {user_facing_gemini_error(exc)}") from exc

    def judge_section(self, *, section_text: str, candidates: list[dict]) -> dict[str, JudgeResult]:
        manifest = "\n".join(
            f"- {candidate['candidate_id']}: {candidate.get('reason', '')}"
            for candidate in candidates
        )
        prompt = f"""Compare all candidate source images for this DeepNote section.

Prefer diagrams, charts, demonstrations, code, UI, whiteboards, and direct evidence.
Reject talking heads, logos, title cards, decoration, repeated imagery, and redundant text.
No visual is a valid recommendation. Rank candidates relative to one another.

Section:
{section_text[:6000]}

Candidates, in the same order as attached images:
{manifest}

Return JSON only:
{{"results":[{{"candidate_id":"...","decision":"use|weak|reject","confidence":"high|medium|low","reason":"short explanation"}}]}}
"""
        contents: list[object] = [prompt]
        for candidate in candidates:
            image_path = Path(str(candidate["_image_path"]))
            mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
            contents.append(f"Candidate {candidate['candidate_id']}")
            contents.append(self._types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime))
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=contents,
                config=self._types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            raw = json.loads((response.text or "{}").strip())
            parsed: dict[str, JudgeResult] = {}
            for result in raw.get("results", []):
                candidate_id = str(result.get("candidate_id", ""))
                if not candidate_id:
                    continue
                decision = str(result.get("decision", "reject")).lower()
                confidence = str(result.get("confidence", "low")).lower()
                if decision not in {"use", "weak", "reject"}:
                    decision = "reject"
                if confidence not in {"high", "medium", "low"}:
                    confidence = "low"
                parsed[candidate_id] = JudgeResult(
                    decision, confidence, str(result.get("reason", ""))[:500],  # type: ignore[arg-type]
                )
            return parsed
        except Exception as exc:  # pragma: no cover - live provider boundary
            raise RuntimeError(f"Gemini visual judge failed: {user_facing_gemini_error(exc)}") from exc


def judge_candidates(
    note_path: Path,
    sidecar_path: Path,
    judge: VisualJudge,
    section_headings: list[str] | None = None,
) -> None:
    markdown = note_path.read_text(encoding="utf-8")
    data = _read_sidecar(sidecar_path)
    grouped: dict[str, list[dict]] = {}
    for candidate in data.get("candidates", []):
        grouped.setdefault(str(candidate.get("section_heading", "")), []).append(candidate)
    for heading, candidates in grouped.items():
        if section_headings is not None and heading not in section_headings:
            continue
        section = _section_text(markdown, heading)
        prepared: list[dict] = []
        for candidate in candidates:
            asset = Path(str(candidate.get("asset_path", "")))
            if not asset.is_absolute():
                asset = Path.cwd() / asset
            prepared.append({**candidate, "_image_path": str(asset)})
        comparative = getattr(judge, "judge_section", None)
        if callable(comparative):
            results = comparative(section_text=section, candidates=prepared)
        else:
            results = {
                candidate["candidate_id"]: judge.judge(
                    section_text=section,
                    image_path=Path(candidate["_image_path"]),
                    reason=str(candidate.get("reason", "")),
                )
                for candidate in prepared
            }
        for candidate in candidates:
            result = results.get(str(candidate.get("candidate_id", "")), JudgeResult("reject", "low", "No judge result."))
            signals = candidate.setdefault("signals", {})
            signals["judge_model"] = judge.model
            signals["judge_decision"] = result.decision
            signals["judge_confidence"] = result.confidence
            signals["judge_reason"] = result.reason
    _write_sidecar(data, sidecar_path)


def approve_and_render(note_path: Path, sidecar_path: Path, candidate_ids: list[str]) -> None:
    data = _read_sidecar(sidecar_path)
    approved_ids = set(candidate_ids)
    reviewed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    reviews: list[VisualReview] = []
    for candidate in data.get("candidates", []):
        candidate_id = str(candidate.get("candidate_id", ""))
        approval = candidate.setdefault("approval", {})
        if candidate_id in approved_ids:
            approval["status"] = "approved"
            approval["reviewed_at"] = reviewed_at
        if approval.get("status") != "approved":
            continue
        reviews.append(VisualReview(
            section_heading=str(candidate["section_heading"]),
            asset_path=str(candidate["asset_path"]),
            alt=str(candidate.get("alt") or "来源视觉证据"),
            status="approved",
        ))

    markdown = note_path.read_text(encoding="utf-8")
    rendered = render_approved_visuals(markdown, reviews)
    note_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")
    _write_sidecar(data, sidecar_path)


def _section_text(markdown: str, heading: str) -> str:
    match = re.search(rf"(?m)^{re.escape(heading)}\s*$", markdown)
    if match is None:
        raise ValueError(f"visual review section not found: {heading}")
    next_heading = re.search(r"(?m)^### .+$", markdown[match.end():])
    end = match.end() + next_heading.start() if next_heading else len(markdown)
    return markdown[match.start():end]


def _read_sidecar(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_sidecar(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
