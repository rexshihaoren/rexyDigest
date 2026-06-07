"""Strict Rex-native KnowledgeCard deep-note formatting."""

from __future__ import annotations

import pytest

from rexy.generate.deep_note_format import prepare_deep_note_markdown, validate_deep_note_markdown


STRICT_NOTE = """# 世界模型正在变成 AI 的实验室

> 整理者：Rex Ren

──────────────────────────────

Source: arXiv
Original Title: World Model Eval
Author: A
ItemID: arxiv:2605.15185

---

### 00｜为什么在意这篇

- 直觉：这篇把 world model 从概念拉回到可验证的实验环境。
- 它戳中的变化：AI 正在从回答问题走向试跑世界。
- 持续观察的方向：仿真环境能否成为 agent 学习现实的中间层。

---

### 01｜尝试回答的问题

- 长期问题：智能体如何在行动前理解世界状态和后果。
- 急迫性：agent 越接近真实任务，纯文本推理越不够。
- 切入点：用可重复的 simulation eval 检查 world model 是否稳定。

---

### 02｜创新点

- 关键论点：真正的增量是把世界理解变成可反复试跑的接口。
- 为什么成立：评测不只看回答对错，也看模型能否维持环境一致性。
- 我的视角：我更在意的是它把“理解世界”变成了工程闭环。

---

### 03｜与 AI X Simulation 的关系

- 连接点：AI 提供策略和预测，simulation 提供可反馈的世界。
- 重要性：两者接上后，agent 能先在环境里试错，而不是直接赌输出。
- 还差一步：还需要证明这种评测能迁移到开放现实任务。

---

### 04｜关键论据

- 支撑材料：作者使用一组环境诊断任务来观察模型行为。
- 最可信的点：评测关注过程一致性，而不是只看最终答案。
- 可被challenge：如果环境太简化，结果可能高估真实世界能力。

---

### 05｜习惯性反思

- 还没说清：它没有完全解释 simulation 和现实之间的 gap。
- 不能推出：不能直接说拥有 world model 就等于能可靠行动。
- 容易误读：不要把 benchmark 提升当成真实智能已经解决。

---

### 06｜沉淀一下

- 一个判断：AI 的下一层竞争会转向可验证的世界接口。
- 可复用的视角：看 agent 工作时，先问它有没有可试错环境。
- 继续追的问题：simulation eval 如何和真实反馈持续校准。

---

### 参考文献

- World Model Eval, A, https://example.com/world-model
"""


def test_prepare_accepts_strict_rex_native_note() -> None:
    assert prepare_deep_note_markdown(STRICT_NOTE) == STRICT_NOTE
    assert validate_deep_note_markdown(STRICT_NOTE) == []


def test_prepare_repairs_safe_formatting_variants() -> None:
    rough = STRICT_NOTE.replace(
        "# 世界模型正在变成 AI 的实验室",
        "Preface from model.\n\n# 世界模型正在变成 AI 的实验室",
    )
    rough = rough.replace("> 整理者：Rex Ren", "整理者：Someone Else")
    rough = rough.replace("──────────────────────────────", "")
    rough = rough.replace("---", "———", 1)

    prepared = prepare_deep_note_markdown(rough)

    assert prepared.startswith("# 世界模型正在变成 AI 的实验室\n")
    assert "> 整理者：Rex Ren" in prepared
    assert "──────────────────────────────" in prepared
    assert "\n---\n" in prepared


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        (STRICT_NOTE.replace("# 世界模型正在变成 AI 的实验室", "# World Model Eval"), "Chinese judgment"),
        (STRICT_NOTE.replace("Source: arXiv\n", ""), "Source"),
        (STRICT_NOTE.replace("Original Title: World Model Eval\n", ""), "Original Title"),
        (STRICT_NOTE.replace("Author: A\n", ""), "Author"),
        (STRICT_NOTE.replace("ItemID: arxiv:2605.15185\n", ""), "ItemID"),
        (STRICT_NOTE.replace("Source: arXiv", "Source: https://example.com/world-model"), "Source must be human-readable"),
        (STRICT_NOTE.replace("### 参考文献", "### 参考"), "参考文献"),
        (STRICT_NOTE.replace("https://example.com/world-model", "data:image/png;base64,abc"), "base64"),
        (STRICT_NOTE + "\n[generator error: failed]\n", "generator error"),
    ],
)
def test_prepare_rejects_invalid_or_unsafe_notes(broken: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        prepare_deep_note_markdown(broken)


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        (STRICT_NOTE.replace("### 00｜为什么在意这篇", "### 00｜为什么我在意这篇"), "missing section"),
        (STRICT_NOTE.replace("- 直觉：", "- Rex 直觉："), "missing bullet"),
        (STRICT_NOTE.replace("- 急迫性：", "- 为什么急："), "missing bullet"),
        (STRICT_NOTE.replace("- 关键论点：", "- 它真正提出的是："), "missing bullet"),
        (STRICT_NOTE.replace("- 可被challenge：", "- 还可以追问："), "missing bullet"),
        (STRICT_NOTE.replace("- 一个判断：", "- 一句话："), "missing bullet"),
    ],
)
def test_prepare_rejects_notes_missing_locked_structure(broken: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        prepare_deep_note_markdown(broken)


def test_prepare_requires_exactly_one_personal_view_in_02_or_03() -> None:
    missing = STRICT_NOTE.replace("- 我的视角：我更在意的是它把“理解世界”变成了工程闭环。\n", "")
    with pytest.raises(ValueError, match="exactly one 我的视角"):
        prepare_deep_note_markdown(missing)

    duplicated = STRICT_NOTE.replace(
        "- 还差一步：还需要证明这种评测能迁移到开放现实任务。",
        "- 还差一步：还需要证明这种评测能迁移到开放现实任务。\n- 我的视角：这里也有一个判断。",
    )
    with pytest.raises(ValueError, match="exactly one 我的视角"):
        prepare_deep_note_markdown(duplicated)

    wrong_section = STRICT_NOTE.replace(
        "- 我的视角：我更在意的是它把“理解世界”变成了工程闭环。\n",
        "",
    ).replace(
        "- 最可信的点：评测关注过程一致性，而不是只看最终答案。",
        "- 最可信的点：评测关注过程一致性，而不是只看最终答案。\n- 我的视角：这个判断放错了位置。",
    )
    with pytest.raises(ValueError, match="only allowed in 02 or 03"):
        prepare_deep_note_markdown(wrong_section)


def test_prepare_rejects_inline_numeric_citations_in_body() -> None:
    broken = STRICT_NOTE.replace("可验证的实验环境。", "可验证的实验环境。[1]", 1)

    with pytest.raises(ValueError, match="inline numeric citation"):
        prepare_deep_note_markdown(broken)


def test_prepare_rejects_old_bilingual_template_shape() -> None:
    broken = """# World Model Eval

> 整理者：Rex Ren

──────────────────────────────

Source: https://example.com/world-model
Author: A
ItemID: rss:test

引言：聚焦世界模型评测机制与可核验诊断信号。
- 世界模型评测 World Model Evaluation
- 几何一致性 Geometric Consistency
- 智能体仿真 Agent Simulation

参考文献: World Model Eval. A. https://example.com/world-model.

---

## Core claim | Chinese / English

**中文**
这是一条基于来源的中文总结。[1]

**English**
This is a grounded English summary. [1]

---

**参考文献**
[1] World Model Eval. A. https://example.com/world-model.
"""

    with pytest.raises(ValueError, match="Chinese judgment"):
        prepare_deep_note_markdown(broken)
