"""Strict Rex-native KnowledgeCard deep-note formatting."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from rexy.generate.deep_note_format import (
    normalize_deep_note_markdown,
    prepare_deep_note_markdown,
    validate_deep_note_markdown,
    validate_review_markdown,
)
from rexy.generate.llm.deep_note import MemoryDeepNoteWriter


STRICT_NOTE = """# 世界模型正在变成 AI 的实验室

> 整理者：Rex Ren

──────────────────────────────

Source: arXiv
Original Title: World Model Eval
Author: A

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


def _prepare_legacy(markdown: str) -> str:
    normalized = normalize_deep_note_markdown(markdown)
    errors = validate_deep_note_markdown(normalized)
    if errors:
        raise ValueError("; ".join(errors))
    return normalized


def test_legacy_note_can_be_reviewed_but_not_generated() -> None:
    assert validate_deep_note_markdown(STRICT_NOTE) == []
    with pytest.raises(ValueError, match="missing section: ### 00｜钩子与变化"):
        prepare_deep_note_markdown(STRICT_NOTE)


def test_prepare_repairs_safe_formatting_variants() -> None:
    rough = STRICT_NOTE.replace(
        "# 世界模型正在变成 AI 的实验室",
        "Preface from model.\n\n# 世界模型正在变成 AI 的实验室",
    )
    rough = rough.replace("> 整理者：Rex Ren", "整理者：Someone Else")
    rough = rough.replace("──────────────────────────────", "")
    rough = rough.replace("---", "———", 1)

    prepared = _prepare_legacy(rough)

    assert prepared.startswith("# 世界模型正在变成 AI 的实验室\n")
    assert "> 整理者：Rex Ren" in prepared
    assert "──────────────────────────────" in prepared
    assert "\n---\n" in prepared


def test_prepare_repairs_known_bullet_label_aliases() -> None:
    rough = STRICT_NOTE
    rough = rough.replace("- 为什么成立：", "- 为什么这个判断成立：")
    rough = rough.replace("- 重要性：", "- 为什么重要：")
    rough = rough.replace("- 支撑材料：", "- 证据材料：")

    raw_errors = validate_deep_note_markdown(rough)
    assert "missing bullet 为什么成立 in ### 02｜创新点" in raw_errors
    assert "missing bullet 重要性 in ### 03｜与 AI X Simulation 的关系" in raw_errors
    assert "missing bullet 支撑材料 in ### 04｜关键论据" in raw_errors

    prepared = _prepare_legacy(rough)

    assert "- 为什么成立：评测不只看回答对错，也看模型能否维持环境一致性。" in prepared
    assert "- 为什么这个判断成立：" not in prepared
    assert "- 重要性：两者接上后，agent 能先在环境里试错，而不是直接赌输出。" in prepared
    assert "- 为什么重要：" not in prepared
    assert "- 支撑材料：作者使用一组环境诊断任务来观察模型行为。" in prepared
    assert "- 证据材料：" not in prepared


def test_prepare_accepts_required_bullet_with_nested_content() -> None:
    rough = STRICT_NOTE.replace(
        "- 支撑材料：作者使用一组环境诊断任务来观察模型行为。",
        "- 支撑材料：\n    * **Vending Bench**：模拟自动售货机运营。\n    * **Project Vend**：真实办公室部署。",
    )

    assert _prepare_legacy(rough) == rough


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        (STRICT_NOTE.replace("# 世界模型正在变成 AI 的实验室", "# World Model Eval"), "Chinese judgment"),
        (STRICT_NOTE.replace("Source: arXiv\n", ""), "Source"),
        (STRICT_NOTE.replace("Original Title: World Model Eval\n", ""), "Original Title"),
        (STRICT_NOTE.replace("Author: A\n", ""), "Author"),
        (STRICT_NOTE.replace("Author: A", "Author: A\nItemID: arxiv:2605.15185"), "ItemID metadata is not allowed"),
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
def test_legacy_validator_rejects_notes_missing_locked_structure(broken: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _prepare_legacy(broken)


def test_review_validation_allows_an_alternate_note_structure() -> None:
    alternate = """# 从 world model 到可行动的判断

这篇不是在证明模型已经理解世界，而是在提供一种更严苛的试错方式。

## 值得带走的东西

1. 评测要看过程一致性。
2. simulation 是行动前的低成本试错场。

## 仍然未知

- 简化环境能否迁移到现实。
"""

    assert validate_review_markdown(alternate) == []


def test_review_validation_rejects_empty_or_unsafe_markdown() -> None:
    assert validate_review_markdown("\n \n") == ["Markdown must not be empty"]
    assert validate_review_markdown("[generator error: failed]") == [
        "contains generator error fallback text"
    ]


def test_prepare_requires_exactly_one_personal_view_in_02_or_03() -> None:
    missing = STRICT_NOTE.replace("- 我的视角：我更在意的是它把“理解世界”变成了工程闭环。\n", "")
    with pytest.raises(ValueError, match="exactly one 我的视角"):
        _prepare_legacy(missing)

    duplicated = STRICT_NOTE.replace(
        "- 还差一步：还需要证明这种评测能迁移到开放现实任务。",
        "- 还差一步：还需要证明这种评测能迁移到开放现实任务。\n- 我的视角：这里也有一个判断。",
    )
    with pytest.raises(ValueError, match="exactly one 我的视角"):
        _prepare_legacy(duplicated)

    wrong_section = STRICT_NOTE.replace(
        "- 我的视角：我更在意的是它把“理解世界”变成了工程闭环。\n",
        "",
    ).replace(
        "- 最可信的点：评测关注过程一致性，而不是只看最终答案。",
        "- 最可信的点：评测关注过程一致性，而不是只看最终答案。\n- 我的视角：这个判断放错了位置。",
    )
    with pytest.raises(ValueError, match="only allowed in 02 or 03"):
        _prepare_legacy(wrong_section)


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


@pytest.fixture
def draft() -> str:
    return MemoryDeepNoteWriter().write(
        item_id="arxiv:example",
        item_type="paper",
        source="arXiv",
        title="World Model Eval",
        author="A",
        url="https://example.com/world-model",
        payload="",
    )


def test_prepare_accepts_numbered_claims_with_separate_evidence(draft: str) -> None:
    note = draft.replace("- 主张：", "- 主张1：").replace(
        "- 边界：", "- 主张2：美元指标在重复评测中不会饱和。\n- 边界："
    ).replace(
        "- [未验证] 测试写入器没有核验来源中的对比结果。",
        "- 主张1：项目负责人在访谈中描述了一个失败案例。 [二手] [单源] [仅轶事]\n"
        "- 主张2：[未验证] 访谈未提供分数趋势。",
    )
    assert prepare_deep_note_markdown(note) == note
    nested_scopes = note.replace(
        "- 边界：限于状态随行动变化的多步任务。",
        "- 边界：\n    - 主张1限于多步任务。\n    - 主张2限于重复评测。",
    )
    assert prepare_deep_note_markdown(nested_scopes) == nested_scopes

    missing_support = note.replace("- 主张2：[未验证] 访谈未提供分数趋势。\n", "")
    with pytest.raises(ValueError, match="missing evidence.*主张2"):
        prepare_deep_note_markdown(missing_support)

    conflicting_tags = note.replace("[二手]", "[一手] [二手]")
    with pytest.raises(ValueError, match="evidence bullet 1 needs one of"):
        prepare_deep_note_markdown(conflicting_tags)


def test_optional_map_requires_two_points_when_present(draft: str) -> None:
    assert prepare_deep_note_markdown(draft) == draft
    heading = "### 05｜沉淀"
    thin_map = "### 04｜与我的地图的关系\n\n- 放入仿真评估的观察清单。\n\n"
    with pytest.raises(ValueError, match="requires two bullets"):
        prepare_deep_note_markdown(draft.replace(heading, thin_map + heading))
    full_map = thin_map.rstrip() + "\n- 优先比较不同交互界面。\n\n---\n\n"
    note = draft.replace(heading, full_map + heading)
    assert prepare_deep_note_markdown(note) == note


def test_prepare_checks_synthesis_and_warns_on_repetition(draft: str, caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(ValueError, match="expected one non-empty 待验证预测"):
        prepare_deep_note_markdown(draft.replace("- 待验证预测：", "- 后续："))
    with pytest.raises(ValueError, match="must be a question or an if-then"):
        prepare_deep_note_markdown(draft.replace("出现吗？", "出现。"))

    claim = next(line.removeprefix("- 主张：") for line in draft.splitlines() if line.startswith("- 主张："))
    repeated = draft.replace("同一个失败换一套交互界面还会出现吗？", claim.rstrip("。") + "？")
    assert prepare_deep_note_markdown(repeated) == repeated
    assert "可复用的视角 may restate a core claim" in caplog.text


def test_prepare_normalizes_current_labels_within_their_sections(draft: str) -> None:
    rough = draft.replace("- 边界：", "- 适用范围：").replace("- 最强反解释：", "- 最强替代解释：")
    assert prepare_deep_note_markdown(rough) == draft


@pytest.mark.parametrize("label", ["边界", "最强反解释"])
def test_new_draft_requires_scope_and_competing_explanation(draft: str, label: str) -> None:
    incomplete = "\n".join(
        line for line in draft.splitlines() if not line.startswith(f"- {label}：")
    )
    with pytest.raises(ValueError, match=f"expected one non-empty {label} bullet"):
        prepare_deep_note_markdown(incomplete)


def test_new_prediction_accepts_future_deadline_but_saved_notes_can_age(draft: str) -> None:
    today = date.today()
    tomorrow = (today + timedelta(days=1)).isoformat()
    dated = draft.replace("- 待验证预测：", f"- 待验证预测：在 {tomorrow} 前，")
    assert prepare_deep_note_markdown(dated) == dated

    yesterday = (today - timedelta(days=1)).isoformat()
    for stale_deadline in (today.isoformat(), yesterday):
        stale = dated.replace(tomorrow, stale_deadline)
        with pytest.raises(ValueError, match="deadline must be after"):
            prepare_deep_note_markdown(stale)
        assert validate_deep_note_markdown(stale) == []


@pytest.mark.parametrize(
    ("deadline", "message"),
    [
        ("2025年底", "must use YYYY-MM-DD"),
        ("2025/12/31", "must use YYYY-MM-DD"),
        ("2099-02-29", "invalid calendar date"),
    ],
)
def test_new_prediction_rejects_ambiguous_or_invalid_deadline(
    draft: str, deadline: str, message: str
) -> None:
    dated = draft.replace("- 待验证预测：", f"- 待验证预测：在 {deadline} 前，")
    with pytest.raises(ValueError, match=message):
        prepare_deep_note_markdown(dated)
