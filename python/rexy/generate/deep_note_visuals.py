"""Render explicitly approved visual evidence into DeepNote Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


ReviewStatus = Literal["pending", "approved", "rejected", "no_visual", "stale"]


@dataclass(frozen=True, slots=True)
class VisualReview:
    section_heading: str
    asset_path: str
    alt: str
    status: ReviewStatus


def render_approved_visuals(markdown: str, reviews: list[VisualReview]) -> str:
    """Insert approved images after their supported section's prose.

    Candidate metadata stays outside Markdown. Non-approved decisions are
    intentionally invisible to downstream publishers.
    """

    approved = [review for review in reviews if review.status == "approved"]
    if not approved:
        return markdown

    rendered = markdown
    for review in approved:
        rendered = _insert_visual(rendered, review)
    return rendered


def _insert_visual(markdown: str, review: VisualReview) -> str:
    if not review.section_heading.startswith("### "):
        raise ValueError("visual review requires an exact DeepNote section heading")
    if not review.asset_path or review.asset_path.lower().startswith("data:image/"):
        raise ValueError("visual review requires a non-base64 asset path")

    heading_pattern = rf"(?m)^{re.escape(review.section_heading)}\s*$"
    heading = re.search(heading_pattern, markdown)
    if heading is None:
        raise ValueError(f"visual review section not found: {review.section_heading}")

    next_heading = re.search(r"(?m)^### .+$", markdown[heading.end():])
    section_end = heading.end() + next_heading.start() if next_heading else len(markdown)
    section = markdown[heading.end():section_end]
    delimiters = list(re.finditer(r"(?m)^---\s*$", section))
    insertion = heading.end() + (delimiters[-1].start() if delimiters else len(section))

    alt = review.alt.replace("[", "").replace("]", "").strip() or "来源视觉证据"
    image = f"![{alt}]({review.asset_path})"
    if image in markdown:
        return markdown
    before = markdown[:insertion].rstrip()
    after = markdown[insertion:].lstrip("\n")
    return f"{before}\n\n{image}\n\n{after}"
