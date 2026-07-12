"""Approved visual evidence is rendered into DeepNote Markdown."""

from __future__ import annotations

from rexy.generate.deep_note_format import validate_deep_note_markdown
from rexy.generate.deep_note_visuals import VisualReview, render_approved_visuals
from rexy.generate.llm.deep_note import MemoryDeepNoteWriter


def _previous_deep_note_shape() -> str:
    return MemoryDeepNoteWriter().write(
        item_id="url-sha1:8ec3bd7b96f13cda",
        item_type="podcast",
        source="Latent Space",
        title="Reality: The Final Eval",
        author="Latent Space",
        url="https://www.latent.space/p/andon",
        payload="Timestamped transcript about Project Vend and Vending Bench.",
    )


def test_previous_deep_note_renders_only_approved_visual_in_supported_section() -> None:
    """Characterization slice for the previous seven-section DeepNote shape."""

    rendered = render_approved_visuals(
        _previous_deep_note_shape(),
        [
            VisualReview(
                section_heading="### 03｜与 AI X Simulation 的关系",
                asset_path="assets/visuals/andon/frame_000993_a1b2c3d4.jpg",
                alt="Project Vend 自动售货机",
                status="approved",
            ),
            VisualReview(
                section_heading="### 04｜关键论据",
                asset_path="assets/visuals/andon/frame_002668_e5f6a7b8.jpg",
                alt="Vending Bench Arena",
                status="pending",
            ),
        ],
    )

    approved = "![Project Vend 自动售货机](assets/visuals/andon/frame_000993_a1b2c3d4.jpg)"
    assert rendered.count(approved) == 1
    assert "frame_002668_e5f6a7b8.jpg" not in rendered
    assert rendered.index(approved) > rendered.index("### 03｜与 AI X Simulation 的关系")
    assert rendered.index(approved) < rendered.index("### 04｜关键论据")
    assert validate_deep_note_markdown(rendered) == []


def test_no_approved_visual_preserves_markdown_byte_for_byte() -> None:
    markdown = _previous_deep_note_shape()
    assert render_approved_visuals(markdown, []) == markdown
