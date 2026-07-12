"""Resolve YouTube provenance and extract section-bounded visual evidence."""

from __future__ import annotations

import html
import hashlib
import json
import re
import subprocess
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PageFetcher = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[list[str]], CommandResult]


@dataclass(frozen=True, slots=True)
class KeyframeCandidate:
    section_heading: str
    timestamp_seconds: int
    source_url: str
    timestamp_url: str
    asset_path: Path
    reason: str


@dataclass(frozen=True, slots=True)
class VisualEnrichmentResult:
    complete: bool
    source_url: str
    candidates: list[KeyframeCandidate]
    error: str = ""


@dataclass(frozen=True, slots=True)
class _TimedText:
    seconds: int
    text: str


_YOUTUBE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?[^\s\"'<>]*v=|embed/|shorts/)|youtu\.be/)"
    r"([0-9A-Za-z_-]{11})[^\s\"'<>]*",
    re.IGNORECASE,
)
_TIMED_TEXT_RE = re.compile(
    r"(?:\[|^|\s)(?P<time>(?:\d{1,2}:)?\d{1,2}:\d{2})(?:\]|\s*[:-])\s*(?P<text>[^\n]+)"
)
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9_-]{2,}", re.IGNORECASE)
_STOPWORDS = {
    "about", "after", "agent", "agents", "also", "from", "into", "that",
    "their", "this", "with", "world", "simulation", "section", "source",
}


def resolve_youtube_url(
    canonical_url: str,
    payload: str,
    fetch_page: PageFetcher | None,
) -> str | None:
    """Return canonical original YouTube URL without fabricating provenance."""

    for content in (canonical_url, payload):
        resolved = _youtube_url_in(content)
        if resolved:
            return resolved
    if fetch_page is None or not canonical_url.startswith(("http://", "https://")):
        return None
    try:
        page = fetch_page(canonical_url)
    except Exception:
        return None
    return _youtube_url_in(html.unescape(page).replace("\\/", "/"))


def fetch_source_page(url: str, timeout_seconds: float = 15.0) -> str:
    """Fetch an Item page only to recover explicit embedded video provenance."""

    request = urllib.request.Request(url, headers={"User-Agent": "rexyDigest/0.1"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def generate_section_keyframes(
    *,
    note_markdown: str,
    payload: str,
    youtube_url: str,
    output_dir: Path,
    runner: CommandRunner | None = None,
) -> VisualEnrichmentResult:
    """Download video and extract scene/fallback frames near relevant evidence."""

    run = runner or _run_command
    output_dir.mkdir(parents=True, exist_ok=True)
    template = output_dir / "source.%(ext)s"
    acquired = run([
        "yt-dlp", "--no-playlist", "--merge-output-format", "mp4",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]", "-o", str(template),
        youtube_url,
    ])
    if acquired.returncode != 0:
        return VisualEnrichmentResult(
            complete=False,
            source_url=youtube_url,
            candidates=[],
            error=_command_error("video acquisition failed", acquired),
        )
    video = _find_video(output_dir)
    if video is None:
        return VisualEnrichmentResult(False, youtube_url, [], "video acquisition produced no media file")

    timed_text = _parse_timed_text(payload)
    sections = _sections(note_markdown)
    candidates: list[KeyframeCandidate] = []
    seen_frame_hashes: set[str] = set()
    for heading, section_text in sections:
        evidence = _best_evidence(section_text, timed_text)
        if evidence is None:
            continue
        window_start = max(0, evidence.seconds - 12)
        window_end = evidence.seconds + 30
        scene = run([
            "ffmpeg", "-hide_banner", "-ss", str(window_start),
            "-t", str(window_end - window_start), "-i", str(video),
            "-vf", "select='gt(scene,0.30)',showinfo", "-an", "-f", "null", "-",
        ])
        relative_times = _scene_times(scene.stderr) if scene.returncode == 0 else []
        timestamp = window_start + int(relative_times[0]) if relative_times else evidence.seconds
        asset = output_dir / f"frame_{timestamp:06d}_{_section_number(heading)}.jpg"
        extracted = run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(timestamp),
            "-i", str(video), "-frames:v", "1", "-q:v", "2", "-y", str(asset),
        ])
        if extracted.returncode != 0 or not asset.exists():
            continue
        frame_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
        if frame_hash in seen_frame_hashes:
            asset.unlink()
            continue
        seen_frame_hashes.add(frame_hash)
        candidates.append(KeyframeCandidate(
            section_heading=heading,
            timestamp_seconds=timestamp,
            source_url=youtube_url,
            timestamp_url=_timestamp_url(youtube_url, timestamp),
            asset_path=asset,
            reason=(
                f"Matches transcript evidence near {_format_seconds(evidence.seconds)}: "
                f"{evidence.text[:160]}"
            ),
        ))

    return VisualEnrichmentResult(True, youtube_url, candidates)


def write_candidate_sidecar(result: VisualEnrichmentResult, path: Path) -> None:
    """Persist internal evidence; publishing consumes none of these fields."""

    data = {
        "schema_version": 1,
        "complete": result.complete,
        "source_url": result.source_url,
        "error": result.error,
        "candidates": [
            {
                "candidate_id": _candidate_id(candidate),
                "section_heading": candidate.section_heading,
                "source_url": candidate.source_url,
                "timestamp_seconds": candidate.timestamp_seconds,
                "timestamp_url": candidate.timestamp_url,
                "asset_path": str(candidate.asset_path),
                "alt": f"{_section_number(candidate.section_heading)} 节来源视觉证据",
                "reason": candidate.reason,
                "signals": {},
                "approval": {"status": "pending", "reviewed_at": None},
            }
            for candidate in result.candidates
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _youtube_url_in(content: str) -> str | None:
    match = _YOUTUBE_URL_RE.search(content)
    if not match:
        return None
    return f"https://www.youtube.com/watch?v={match.group(1)}"


def _parse_timed_text(payload: str) -> list[_TimedText]:
    parsed: list[_TimedText] = []
    seen: set[tuple[int, str]] = set()
    for match in _TIMED_TEXT_RE.finditer(payload):
        seconds = _parse_timestamp(match.group("time"))
        text = match.group("text").strip()
        key = (seconds, text)
        if key not in seen:
            parsed.append(_TimedText(seconds, text))
            seen.add(key)
    return parsed


def _parse_timestamp(raw: str) -> int:
    parts = [int(part) for part in raw.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def _sections(markdown: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^### (?:0[0-6]｜.+)$", markdown))
    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        result.append((match.group(0).strip(), markdown[match.end():end]))
    return result


def _best_evidence(section: str, timed_text: list[_TimedText]) -> _TimedText | None:
    section_terms = _terms(section)
    if not section_terms:
        return None
    ranked = [(len(section_terms & _terms(segment.text)), segment) for segment in timed_text]
    score, segment = max(ranked, key=lambda pair: pair[0], default=(0, None))
    return segment if score > 0 else None


def _terms(text: str) -> set[str]:
    return {word.lower() for word in _WORD_RE.findall(text) if word.lower() not in _STOPWORDS}


def _scene_times(stderr: str) -> list[float]:
    return [float(raw) for raw in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", stderr)]


def _section_number(heading: str) -> str:
    match = re.match(r"### (\d{2})", heading)
    return match.group(1) if match else "xx"


def _timestamp_url(url: str, seconds: int) -> str:
    parsed = urlparse(url)
    video_id = parse_qs(parsed.query).get("v", [""])[0]
    return f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"


def _format_seconds(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _candidate_id(candidate: KeyframeCandidate) -> str:
    digest = hashlib.sha256(candidate.asset_path.read_bytes()).hexdigest()[:12]
    video_id = parse_qs(urlparse(candidate.source_url).query).get("v", ["video"])[0]
    return f"youtube:{video_id}:{candidate.timestamp_seconds}:{digest}"


def _find_video(output_dir: Path) -> Path | None:
    return next((path for path in sorted(output_dir.glob("source.*")) if path.is_file()), None)


def _command_error(prefix: str, result: CommandResult) -> str:
    detail = (result.stderr or result.stdout).strip()
    return f"{prefix}: {detail}" if detail else prefix


def _run_command(command: list[str]) -> CommandResult:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        return CommandResult(127, "", f"{exc.filename} unavailable")
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)
