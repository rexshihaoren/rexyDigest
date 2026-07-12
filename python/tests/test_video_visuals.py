"""YouTube provenance and section-bounded keyframe generation."""

from __future__ import annotations

from pathlib import Path

from rexy.generate.video_visuals import (
    CommandResult,
    generate_section_keyframes,
    resolve_youtube_url,
    write_candidate_sidecar,
)


NOTE = """# 测试

### 03｜与 AI X Simulation 的关系

- 连接点：Project Vend 把自动售货机带入真实世界。

---

### 04｜关键论据

- 支撑材料：Vending Bench Arena 展示价格竞争。
"""

PAYLOAD = """
Timestamps 00:16:33 Project Vend: Claude Runs a Real Vending Machine
00:44:28 Lying, Refunds, and Price Cartels in Arena
Transcript
Swyx [00:16:33]: Let us talk about Project Vend and the real vending machine.
Axel [00:44:28]: Vending Bench Arena showed price competition and cartels.
"""


def test_resolves_direct_and_embedded_original_youtube_urls() -> None:
    direct = "https://www.youtube.com/watch?v=abc12345678"
    assert resolve_youtube_url(direct, "", None) == direct

    html = '<iframe src="https://www.youtube.com/embed/xyz12345678"></iframe>'
    assert resolve_youtube_url("https://example.com/post", "", lambda _url: html) == (
        "https://www.youtube.com/watch?v=xyz12345678"
    )


def test_generates_timestamped_keyframes_in_each_relevant_section_window(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(command: list[str]) -> CommandResult:
        calls.append(command)
        if command[0] == "yt-dlp":
            Path(command[command.index("-o") + 1].replace("%(ext)s", "mp4")).write_bytes(b"video")
            return CommandResult(0, "", "")
        if command[0] == "ffmpeg" and "showinfo" in " ".join(command):
            return CommandResult(0, "", "showinfo pts_time:3.0")
        if command[0] == "ffmpeg":
            Path(command[-1]).write_bytes(("frame:" + command[command.index("-ss") + 1]).encode())
            return CommandResult(0, "", "")
        raise AssertionError(command)

    result = generate_section_keyframes(
        note_markdown=NOTE,
        payload=PAYLOAD,
        youtube_url="https://www.youtube.com/watch?v=abc12345678",
        output_dir=tmp_path,
        runner=runner,
    )

    assert result.complete is True
    assert {candidate.section_heading for candidate in result.candidates} == {
        "### 03｜与 AI X Simulation 的关系",
        "### 04｜关键论据",
    }
    assert result.candidates[0].timestamp_url.startswith(
        "https://www.youtube.com/watch?v=abc12345678&t="
    )
    assert all(candidate.asset_path.exists() for candidate in result.candidates)
    assert any("showinfo" in " ".join(command) for command in calls)

    sidecar = tmp_path / "candidates.json"
    write_candidate_sidecar(result, sidecar)
    text = sidecar.read_text(encoding="utf-8")
    assert '"source_url": "https://www.youtube.com/watch?v=abc12345678"' in text
    assert '"timestamp_url": "https://www.youtube.com/watch?v=abc12345678&t=' in text


def test_provider_failure_keeps_text_path_usable(tmp_path: Path) -> None:
    result = generate_section_keyframes(
        note_markdown=NOTE,
        payload=PAYLOAD,
        youtube_url="https://www.youtube.com/watch?v=abc12345678",
        output_dir=tmp_path,
        runner=lambda _command: CommandResult(1, "", "yt-dlp unavailable"),
    )

    assert result.complete is False
    assert result.candidates == []
    assert "yt-dlp unavailable" in result.error


def test_duplicate_frame_is_not_repeated_across_sections(tmp_path: Path) -> None:
    def runner(command: list[str]) -> CommandResult:
        if command[0] == "yt-dlp":
            Path(command[command.index("-o") + 1].replace("%(ext)s", "mp4")).write_bytes(b"video")
        elif command[0] == "ffmpeg" and "showinfo" not in " ".join(command):
            Path(command[-1]).write_bytes(b"same pixels")
        return CommandResult(0, "", "")

    result = generate_section_keyframes(
        note_markdown=NOTE,
        payload=PAYLOAD,
        youtube_url="https://www.youtube.com/watch?v=abc12345678",
        output_dir=tmp_path,
        runner=runner,
    )

    assert len(result.candidates) == 1
    assert len(list(tmp_path.glob("frame_*.jpg"))) == 1
