"""Bilingual public-brief renderer.

Output is a deterministic Python render that keeps the legacy public identity
without publish-time LLM calls. Differences from the old Node prompt transform:

  - No LLM round-trip — Chinese fields come straight from
    `SelectionEntry.translations`. If a translation is missing the EN
    version is used as a transparent fallback (rather than fabricating CN).
  - No `MODEL_FALLBACKS` chain to maintain.
  - Deterministic: same input JSONL -> byte-identical output.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..domain import Item, SelectionEntry, Window


_TYPE_EMOJI = {
    "paper": "📄",
    "blog": "📝",
    "podcast": "🎙",
    "video": "📺",
    "talk": "🎤",
}
_TYPE_CN = {
    "paper": "论文",
    "blog": "博客",
    "podcast": "播客",
    "video": "视频",
    "talk": "演讲",
}
_PUBLIC_ITEM_LIMIT = 5
_OVERVIEW_ITEM_LIMIT = 3


def render_public_brief(
    window: Window,
    entries: Iterable[SelectionEntry],
    items_by_id: dict[str, Item],
) -> str:
    """Return the bilingual public-brief Markdown for one Selection."""

    public_entries = select_public_entries(entries)
    end = window.end.isoformat()
    lines: list[str] = []
    lines.append("# AI×Simulation｜每周雷达")
    lines.append("## 智能体×世界模型｜本周严选：论文·视频·博文")
    lines.append("")
    lines.append("> 整理者：Rex Ren")
    lines.append("")
    lines.append(_coverage_line(window, len(public_entries)))
    lines.append("")

    overview_block = _render_overview(public_entries, items_by_id)
    if overview_block:
        lines.extend(overview_block)
        lines.append("")

    lines.append("---")

    for entry in public_entries:
        item = items_by_id.get(entry.item_id)
        if item is None:
            continue
        lines.append("")
        lines.extend(_render_entry(entry, item))
        lines.append("---")

    while lines and lines[-1].strip() == "---":
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()

    kol_block = _render_kol_roster(public_entries, items_by_id)
    if kol_block:
        lines.append("")
        lines.append("")
        lines.extend(kol_block)

    return "\n".join(lines).rstrip() + "\n"


def _coverage_line(window: Window, count: int) -> str:
    cn_start = _to_cn_date(window.start.isoformat())
    cn_end = _to_cn_date(window.end.isoformat())
    return (
        f"覆盖范围 Coverage window：**{cn_start} 至 {cn_end}** "
        f"｜ 入选 Items: **{count}**"
    )


def _to_cn_date(s: str) -> str:
    y, m, d = s.split("-")
    return f"{y}年{m}月{d}日"


def select_public_entries(entries: Iterable[SelectionEntry]) -> list[SelectionEntry]:
    """Return Selection rank Top 5 entries rendered in the public Brief body."""

    return sorted(list(entries), key=lambda e: e.rank)[:_PUBLIC_ITEM_LIMIT]


def select_overview_highlights(
    entries: Iterable[SelectionEntry],
    items_by_id: dict[str, Item],
) -> list[tuple[SelectionEntry, Item]]:
    """Return public overview highlights from renderable public body entries."""

    pairs = [(e, items_by_id[e.item_id]) for e in entries if e.item_id in items_by_id]
    return sorted(
        pairs,
        key=lambda pair: (
            0 if _is_mission_or_bridge(pair[0], pair[1]) else 1,
            -pair[0].scores.composite,
            pair[0].rank,
        ),
    )[:_OVERVIEW_ITEM_LIMIT]


def _render_entry(entry: SelectionEntry, item: Item) -> list[str]:
    emoji = _TYPE_EMOJI.get(item.type, "🔗")
    type_cn = _TYPE_CN.get(item.type, item.type)
    type_en = item.type.capitalize() or "Item"

    title_zh = entry.translations.title_zh or item.title
    tldr_zh = entry.translations.tldr_zh or entry.tldr_en
    impl_zh = entry.translations.implication_zh or entry.implication_en
    takeaways_zh = entry.translations.takeaways_zh or entry.takeaways_en
    topics_zh = entry.translations.topics_zh or entry.topics or ["智能体"]

    out: list[str] = []
    out.append("")
    out.append("**标题｜Title**")
    out.append(
        f"{emoji} **{_safe(item.author)}** — {_safe(title_zh)}（{type_cn}，{item.published_at.isoformat()}） "
        f"｜ {emoji} **{_safe(item.author)}** — {_safe(item.title)} ({type_en}, {item.published_at.isoformat()})"
    )
    out.append("")
    out.append(f"**来源｜Source**：{item.canonical_url}")
    out.append("")
    out.append("**摘要｜TL;DR**")
    out.append(f"{tldr_zh.strip()} ｜ {entry.tldr_en.strip()}")
    out.append("")
    out.append("**要点｜Takeaways**")
    for cn, en in zip(_pad(takeaways_zh, len(entry.takeaways_en)), entry.takeaways_en):
        out.append(f"• {cn.strip()} ｜ {en.strip()}")
    out.append("")
    out.append("**启示｜Implication**")
    out.append(f"{impl_zh.strip()} ｜ {entry.implication_en.strip()}")
    out.append("")
    out.append("**综合评分｜CompositeScore**")
    out.append(f"{entry.scores.composite:.1f}")
    out.append("")
    out.append("**主题｜Topics**")
    out.append(f"{', '.join(topics_zh)} ｜ {', '.join(entry.topics) if entry.topics else 'Agent'}")
    return out


_KOL_TOPIC_PREFIX = "kol:"


def _render_overview(
    entries_list: list[SelectionEntry],
    items_by_id: dict[str, Item],
) -> list[str]:
    """Top 3 highlights, mission/bridge first, then composite and rank."""

    highlights = select_overview_highlights(entries_list, items_by_id)
    if not highlights:
        return []

    out: list[str] = []
    out.append("### 核心看点 Overview（双语）")
    for entry, item in highlights:
        title_zh = entry.translations.title_zh or item.title
        out.append(f"- 🏅 {_safe(title_zh)} ｜ {_safe(item.title)}")
    return out


def _is_mission_or_bridge(entry: SelectionEntry, item: Item) -> bool:
    topics = {topic.strip().lower() for topic in entry.topics}
    if "simulation" in topics:
        return True

    bridge_keywords = (
        "world model", "world models", "digital physics", "simulation-based eval",
        "simulation-based evals", "simulation based eval", "simulation based evals",
        "simulation eval", "simulation evals", "simulation evaluation",
        "simulation evaluations", "synthetic world", "synthetic worlds",
        "consciousness modeling", "epistemic simulation",
    )
    haystack = " ".join([
        item.title,
        item.author,
        item.type,
        " ".join(item.topics_raw),
        entry.tldr_en,
        " ".join(entry.takeaways_en),
        entry.implication_en,
        " ".join(entry.topics),
    ]).lower()
    return any(keyword in haystack for keyword in bridge_keywords)


def _render_kol_roster(
    entries_list: list[SelectionEntry],
    items_by_id: dict[str, Item],
) -> list[str]:
    """List unique KOL slugs (from `kol:*` topic markers) that landed in this brief.

    Slugs are normalised lower-case for stability; ordering follows first
    appearance in the Selection rank order so output is deterministic.
    """

    seen: list[str] = []
    seen_lc: set[str] = set()
    for e in entries_list:
        it = items_by_id.get(e.item_id)
        if it is None:
            continue
        for topic in it.topics_raw or ():
            if not isinstance(topic, str):
                continue
            if not topic.lower().startswith(_KOL_TOPIC_PREFIX):
                continue
            slug = topic[len(_KOL_TOPIC_PREFIX):].strip()
            slug_lc = slug.lower()
            if not slug_lc or slug_lc in seen_lc:
                continue
            seen.append(slug)
            seen_lc.add(slug_lc)
    if not seen:
        return []

    out: list[str] = []
    out.append("---")
    out.append("")
    out.append(
        f"**本周 KOL｜KOL roster**: {', '.join(seen)}"
    )
    return out


def _pad(zh: list[str], target_len: int) -> list[str]:
    if len(zh) >= target_len:
        return zh[:target_len]
    return list(zh) + ["（未翻译）"] * (target_len - len(zh))


def _safe(s: str) -> str:
    return s.replace("|", "/").replace("\n", " ").strip()
