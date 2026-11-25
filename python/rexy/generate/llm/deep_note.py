"""Second-pass LLM: single-topic deep note as Markdown (knowledgecard-ready)."""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Protocol, runtime_checkable

from .gemini_common import resolve_gemini_api_key, user_facing_gemini_error

logger = logging.getLogger(__name__)

_DEEP_PROMPT = """You are writing ONE standalone KnowledgeCard input note for Rex Ren and Chinese readers who track AI x Simulation.

Write in **Markdown only** (no JSON). Audience: same as a personal research card — dense, honest, no clickbait.
The output must be strict KnowledgeCard Markdown and must be ready to save directly to `KnowledgeCard_Inbox/`.

Required exact structure:

# <Chinese judgment title, not the source title>

> 整理者：Rex Ren

──────────────────────────────

Source: <human-readable source>
Original Title: <source title>
Author: <author>

---

### 00｜钩子与变化

- <one concrete scene from the source, when available>
- <one sentence on what changed>

---

### 01｜核心主张

- 主张：<one falsifiable claim>
- 边界：<populations, conditions, or contexts where the claim applies; define ambiguous terms>

---

### 02｜证据

- <named source, specific observation, and its limits> [一手] [单源]

---

### 03｜反方

- 最强反解释：<strongest competing explanation and what observation would distinguish it>

---

### 04｜与我的地图的关系

- <substantive personal connection, explicitly identified as an inference>
- <implication that follows from that connection>

---

### 05｜沉淀

- 可复用的视角：<a reusable question ending with ？ or an explicit if-then heuristic>
- 待验证预测：<an observable outcome and a future deadline or explicit test condition>

---

### 参考文献

- <title>, <author>, <source URL if present>

Rules:
- Ground every factual claim in the payload below; if payload thin, say so explicitly.
- Do not invent URLs, quotes, or paper IDs.
- H1 must be a Chinese judgment sentence. Do not use the source title as H1.
- Use Chinese as the main language. English should be roughly 10% overall, limited to necessary terms such as agent, world model, benchmark, challenge.
- Use the headings in order. Section 04 is optional. When the personal connection only merits a tag,
  replace section 04 with a short tag in one of the one or two opening bullets.
- State the claim once. If it contains independent assertions, replace 主张 with consecutive bullets
  主张1, 主张2, etc. Prefix every evidence bullet with the matching claim label, e.g. 主张1：.
  Use exactly one unnumbered 边界 bullet after all claims. Claim-specific scopes
  may be nested under that bullet. For unsupported claims,
  put [未验证] immediately after the claim label, before the reason. Follow this
  example for layout only; use the actual source for content:

  ### 01｜核心主张
  - 主张1：<first claim>
  - 主张2：<second claim>
  - 边界：主张1限于<scope>；主张2限于<scope>。

  ### 02｜证据
  - 主张1：<observation and limits> [一手] [单源]
  - 主张2：[未验证] <reason evidence is missing>

- Use exactly one provenance tag ([一手] or [二手]) and one source count tag ([单源] or [多源])
  per evidence bullet. Optionally add [有数字] or [仅轶事]. Identify the original source and
  flag missing run counts, denominators, or replication where relevant. Multiple examples from
  one interview are still single-source. If evidence is absent, write [未验证] followed by the
  reason in place of evidence and tags.
- Synthesis must add a reusable test or decision rule and a gradeable prediction.
  Avoid paraphrasing the core claim.
- Generation date: {generation_date}. Use YYYY-MM-DD for any prediction deadline.
  Every such date must be strictly after the generation date. If no calendar
  deadline is justified, give a concrete future test condition instead.
- Do not include inline numeric citations like `[1]` in the body.
- Always include `### 参考文献`; put the URL there, not in metadata.
- Extra references are allowed only if they appear explicitly in the payload.
- Include images only if the payload already contains a real source image URL or local image path.
- Put any image immediately after the section it supports using `(配图: <url-or-path>)`.
- Do not generate images. Do not emit base64 data URIs.
- Do not include ItemID in the Markdown. Internal item ids stay in filenames and deep_picks TOML, not the KnowledgeCard body.
- Length: roughly 1200–1800 Chinese characters unless payload is tiny (then shorter).

Type: {item_type}
Source: {source}
Title: {title}
Author: {author}
URL: {url}

Payload:
\"\"\"
{payload}
\"\"\"
"""


@runtime_checkable
class DeepNoteWriter(Protocol):
    model: str

    def write(
        self,
        *,
        item_id: str,
        item_type: str,
        source: str,
        title: str,
        author: str,
        url: str,
        payload: str,
    ) -> str:
        """Return Markdown body (full note)."""


class GeminiDeepNoteWriter:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None) -> None:
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("google-genai not installed") from exc

        key = resolve_gemini_api_key(api_key)
        if not key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY required for deep notes")
        self._client = genai.Client(api_key=key)
        self._types = genai_types
        self.model = model

    def write(
        self,
        *,
        item_id: str,
        item_type: str,
        source: str,
        title: str,
        author: str,
        url: str,
        payload: str,
    ) -> str:
        text = (payload or "").strip()[:24000]
        rendered = _DEEP_PROMPT.format(
            generation_date=date.today().isoformat(),
            item_id=item_id,
            item_type=item_type,
            source=source,
            title=title,
            author=author,
            url=url,
            payload=text or "(empty)",
        )
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=rendered,
                config=self._types.GenerateContentConfig(temperature=0.35),
            )
            return (response.text or "").strip()
        except Exception as exc:  # pragma: no cover
            logger.warning("Gemini deep note failed for %s (%s)", item_id, type(exc).__name__)
            err = user_facing_gemini_error(exc)
            raise RuntimeError(f"Gemini deep note failed for {item_id}: {err}") from exc


class MemoryDeepNoteWriter:
    """Deterministic stub for tests / smoke without API."""

    model: str = "memory-deep-stub"

    def write(
        self,
        *,
        item_id: str,
        item_type: str,
        source: str,
        title: str,
        author: str,
        url: str,
        payload: str,
    ) -> str:
        return (
            "# 世界模型正在变成 AI 的实验室\n\n"
            "> 整理者：Rex Ren\n\n"
            "──────────────────────────────\n\n"
            f"Source: {source}\n"
            f"Original Title: {title}\n"
            f"Author: {author or 'Unknown'}\n\n"
            "---\n\n"
            "### 00｜钩子与变化\n\n"
            "- 关注同一个任务在文本评测和环境试跑中的差异。\n\n"
            "---\n\n"
            "### 01｜核心主张\n\n"
            "- 主张：加入环境反馈的评测会发现纯文本评测漏掉的失败。\n"
            "- 边界：限于状态随行动变化的多步任务。\n\n"
            "---\n\n"
            "### 02｜证据\n\n"
            "- [未验证] 测试写入器没有核验来源中的对比结果。\n\n"
            "---\n\n"
            "### 03｜反方\n\n"
            "- 最强反解释：失败可能来自交互界面。固定任务和提示词，替换界面后重测。\n\n"
            "---\n\n"
            "### 05｜沉淀\n\n"
            "- 可复用的视角：同一个失败换一套交互界面还会出现吗？\n"
            "- 待验证预测：固定任务和提示词后，至少一种失败会在两套界面下复现。\n\n"
            "---\n\n"
            "### 参考文献\n\n"
            f"- {title}, {author or 'Unknown'}, {url}\n"
            f"<!-- memory stub: type={item_type}; payload chars={len(payload or '')} -->\n"
        )


def safe_filename_part(item_id: str, max_len: int = 80) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", item_id).strip("_")
    return s[:max_len] if len(s) > max_len else s
