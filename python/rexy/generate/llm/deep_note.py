"""Second-pass LLM: single-topic deep note as Markdown (knowledgecard-ready)."""

from __future__ import annotations

import logging
import re
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

### 00｜为什么在意这篇

- 直觉：<LLM draft of Rex's first-principles instinct; Chinese-first, emotionally alive but not melodramatic>
- 它戳中的变化：<what world change this source points to>
- 持续观察的方向：<what Rex should keep watching>

---

### 01｜尝试回答的问题

- 长期问题：<the older unresolved problem>
- 急迫性：<why this is becoming urgent now>
- 切入点：<where this source enters the problem>

---

### 02｜创新点

- 关键论点：<the core new claim>
- 为什么成立：<why the claim is supported by the payload>
- 我的视角：<include this bullet here only if section 02 is the one key personal-view section; otherwise omit this line entirely>

---

### 03｜与 AI X Simulation 的关系

- 连接点：<how AI and simulation connect here>
- 重要性：<why that connection matters>
- 还差一步：<what still needs to happen>
- 我的视角：<include this bullet here only if section 03 is the one key personal-view section; otherwise omit this line entirely>

---

### 04｜关键论据

- 支撑材料：<what evidence/case/argument the source uses>
- 最可信的点：<the strongest grounded part>
- 可被challenge：<where a sharp reader can still challenge it>

---

### 05｜习惯性反思

- 还没说清：<what the source has not clarified>
- 不能推出：<what readers should not conclude>
- 容易误读：<likely misconception>

---

### 06｜沉淀一下

- 一个判断：<one compressed judgment Rex can keep>
- 可复用的视角：<a lens reusable for future items>
- 继续追的问题：<one next question to track>

---

### 参考文献

- <title>, <author>, <source URL if present>

Rules:
- Ground every factual claim in the payload below; if payload thin, say so explicitly.
- Do not invent URLs, quotes, or paper IDs.
- H1 must be a Chinese judgment sentence. Do not use the source title as H1.
- Use Chinese as the main language. English should be roughly 10% overall, limited to necessary terms such as agent, world model, benchmark, challenge.
- Keep exactly the 7 fixed sections plus `### 参考文献`.
- Keep the exact bullet labels shown above.
- Include exactly one `我的视角：` bullet in the body: either section 02 or section 03, not both.
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
            "### 00｜为什么在意这篇\n\n"
            "- 直觉：这条内容把 AI 能力放回到可试错的世界接口里看。\n"
            "- 它戳中的变化：智能体不只需要回答，还需要在环境里验证行动。\n"
            "- 持续观察的方向：world model 和 simulation eval 会不会成为下一层基础设施。\n\n"
            "---\n\n"
            "### 01｜尝试回答的问题\n\n"
            "- 长期问题：智能体如何在真实行动前理解状态、后果和约束。\n"
            "- 急迫性：agent 越接近复杂任务，纯文本推理越容易失真。\n"
            "- 切入点：这条来源用一个具体视角观察 AI 和仿真的连接。\n\n"
            "---\n\n"
            "### 02｜创新点\n\n"
            "- 关键论点：核心不是模型更大，而是把理解世界变成可反复检查的过程。\n"
            "- 为什么成立：来源 payload 给出了足够线索，说明它关心环境反馈而不是单次输出。\n"
            "- 我的视角：我会把它看成 AI 从语言界面走向世界接口的一小步。\n\n"
            "---\n\n"
            "### 03｜与 AI X Simulation 的关系\n\n"
            "- 连接点：AI 负责策略、预测和解释，simulation 提供可反馈的试错场。\n"
            "- 重要性：两者接上后，agent 能在行动前先校准对世界的理解。\n"
            "- 还差一步：还需要证明这种连接能从受控环境迁移到开放任务。\n\n"
            "---\n\n"
            "### 04｜关键论据\n\n"
            "- 支撑材料：来源包含可用于二次整理的摘要或正文片段。\n"
            "- 最可信的点：它至少提供了明确主题，而不是只有标题级信号。\n"
            f"- 可被challenge：当前 payload 长度为 {len(payload or '')} 字符，薄内容需要打折看。\n\n"
            "---\n\n"
            "### 05｜习惯性反思\n\n"
            "- 还没说清：它没有完全说明从仿真到真实世界的落差。\n"
            "- 不能推出：不能直接推出某个 agent 已经具备可靠现实行动能力。\n"
            "- 容易误读：不要把 benchmark 或 demo 的表现等同于稳定智能。\n\n"
            "---\n\n"
            "### 06｜沉淀一下\n\n"
            "- 一个判断：AI 的关键竞争会越来越依赖可验证的世界接口。\n"
            "- 可复用的视角：下次看类似工作，先问它有没有真实反馈闭环。\n"
            "- 继续追的问题：simulation eval 如何持续和现实任务对齐。\n\n"
            "---\n\n"
            "### 参考文献\n\n"
            f"- {title}, {author or 'Unknown'}, {url}\n"
            f"<!-- memory stub: type={item_type}; payload chars={len(payload or '')} -->\n"
        )


def safe_filename_part(item_id: str, max_len: int = 80) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", item_id).strip("_")
    return s[:max_len] if len(s) > max_len else s
