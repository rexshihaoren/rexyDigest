"""Provider-neutral item-analysis prompt and JSON parser."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from . import DEFAULT_LENS, ItemAnalysis, ItemPrompt

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """You are scoring one piece of content for a weekly bilingual brief on AI agents and the simulation hypothesis.

{lens}

Item:
  type:    {item_type}
  title:   {title}
  author:  {author}
  payload (extract or full text, may be empty):
\"\"\"
{payload}
\"\"\"

Return ONLY valid JSON matching this schema:
{{
  "relevance":      <float 1.0-5.0>,
  "actionability":  <float 1.0-5.0>,
  "tldr_en":        <one sentence string, English>,
  "takeaways_en":   [<3-5 short bullet strings, English>],
  "implication_en": <one sentence on why a practitioner-philosopher should care>,
  "topics":         [<one or more of: "Agent", "Simulation">],
  "title_zh":       <Simplified Chinese translation of title>,
  "tldr_zh":        <SC translation of tldr_en>,
  "takeaways_zh":   [<SC translations of each takeaway, same length as takeaways_en>],
  "implication_zh": <SC translation of implication_en>,
  "topics_zh":      [<SC labels: 智能体 | 模拟>]
}}

Rules:
- Be honest. If the payload is empty or weak, score relevance/actionability low.
- "topics" must be a non-empty subset of ["Agent", "Simulation"].
- No markdown, no commentary, JSON only.
"""


def render_item_analysis_prompt(prompt: ItemPrompt) -> str:
    return PROMPT_TEMPLATE.format(
        lens=prompt.lens or DEFAULT_LENS,
        item_type=prompt.item_type,
        title=prompt.title,
        author=prompt.author,
        payload=(prompt.payload or "").strip()[:8000],
    )


def parse_item_analysis_json(item_id: str, text: str, provider: str) -> ItemAnalysis:
    """Parse provider JSON; abort without echoing raw model text."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        stripped = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            logger.warning("%s JSON parse failed for %s (length=%s)", provider, item_id, len(text))
            raise RuntimeError(
                f"{provider} analysis failed for {item_id}: "
                "model returned text that was not valid JSON (check logs / rerun)"
            )

    return ItemAnalysis(
        item_id=item_id,
        relevance=_as_float(data.get("relevance"), default=1.0),
        actionability=_as_float(data.get("actionability"), default=1.0),
        tldr_en=str(data.get("tldr_en") or ""),
        takeaways_en=_as_str_list(data.get("takeaways_en")),
        implication_en=str(data.get("implication_en") or ""),
        topics=_as_str_list(data.get("topics")) or [],
        title_zh=_as_optional_str(data.get("title_zh")),
        tldr_zh=_as_optional_str(data.get("tldr_zh")),
        takeaways_zh=_as_str_list(data.get("takeaways_zh")) or None,
        implication_zh=_as_optional_str(data.get("implication_zh")),
        topics_zh=_as_str_list(data.get("topics_zh")) or None,
    )


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return max(1.0, min(5.0, float(v)))
    except (TypeError, ValueError):
        return default


def _as_str_list(v: Any) -> list[str]:
    if not isinstance(v, list):
        return []
    return [str(x) for x in v if x is not None]


def _as_optional_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None
