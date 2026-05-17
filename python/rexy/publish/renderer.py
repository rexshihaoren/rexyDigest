"""Bilingual public-brief renderer.

Output shape mirrors the Node publisher's "structured" mode (see
`scripts/publize_brief.mjs:buildStructured`) so existing readers don't see
a sudden format break. Differences:

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


def render_public_brief(
    window: Window,
    entries: Iterable[SelectionEntry],
    items_by_id: dict[str, Item],
) -> str:
    """Return the bilingual public-brief Markdown for one Selection."""

    entries_list = list(entries)
    end = window.end.isoformat()
    lines: list[str] = []
    lines.append(f"# Weekly Digest – {end}")
    lines.append("")
    lines.append("> 整理者：Rex Ren")
    lines.append("")
    lines.append(_coverage_line(window, len(entries_list)))
    lines.append("")

    lead_block = _render_lead_block(entries_list, items_by_id)
    if lead_block:
        lines.extend(lead_block)
        lines.append("")

    lines.append("---")

    for entry in entries_list:
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

    kol_block = _render_kol_roster(entries_list, items_by_id)
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


def _render_lead_block(
    entries_list: list[SelectionEntry],
    items_by_id: dict[str, Item],
) -> list[str]:
    """Top-ranked Item as '本周亮点｜Lead' anchor. Empty if no usable entries."""

    lead: SelectionEntry | None = None
    lead_item: Item | None = None
    for e in entries_list:
        it = items_by_id.get(e.item_id)
        if it is not None:
            if lead is None or e.rank < lead.rank:
                lead, lead_item = e, it
    if lead is None or lead_item is None:
        return []

    title_zh = lead.translations.title_zh or lead_item.title
    tldr_zh = (lead.translations.tldr_zh or lead.tldr_en).strip()
    tldr_en = lead.tldr_en.strip()
    out: list[str] = []
    out.append("**本周亮点｜Lead**")
    out.append(
        f"⭐ **{_safe(lead_item.author)}** — {_safe(title_zh)} ｜ {_safe(lead_item.title)}"
    )
    out.append(f"{tldr_zh} ｜ {tldr_en}")
    out.append(f"_综合评分｜CompositeScore: {lead.scores.composite:.1f}_")
    return out


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
