# Public Brief Template

This is the human-readable contract for the current Python public Brief
renderer.
Runtime source of truth: `python/rexy/publish/renderer.py`.

The renderer is deterministic and LLM-free. This file is for human review,
editorial alignment, and template validation tests; it is not parsed at
runtime.

## Output Path

`Weekly_Gist/Public/Weekly_Brief_Public_<end-date>.md`

## Structure

```md
# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**{start_date_zh} 至 {end_date_zh}** ｜ 入选 Items: **{item_count}**

### 核心看点 Overview（双语）
- 🏅 {highlight_title_zh_1} ｜ {highlight_title_en_1}
- 🏅 {highlight_title_zh_2} ｜ {highlight_title_en_2}
- 🏅 {highlight_title_zh_3} ｜ {highlight_title_en_3}

---

**标题｜Title**
{emoji} **{author}** — {title_zh}（{type_zh}，{published_date}） ｜ {emoji} **{author}** — {title_en} ({type_en}, {published_date})

**来源｜Source**：{canonical_url}

**摘要｜TL;DR**
{tldr_zh} ｜ {tldr_en}

**要点｜Takeaways**
• {takeaway_zh_1} ｜ {takeaway_en_1}
• {takeaway_zh_2} ｜ {takeaway_en_2}
• {takeaway_zh_3} ｜ {takeaway_en_3}

**启示｜Implication**
{implication_zh} ｜ {implication_en}

**综合评分｜CompositeScore**
{composite_score}

**主题｜Topics**
{topics_zh} ｜ {topics_en}

---

**本周 KOL｜KOL roster**: {kol_slug_1}, {kol_slug_2}
```

## Rules

- The Selection JSONL is the truth; this Markdown is a deterministic render.
- Public Brief body renders the first five Selection entries by rank.
- Chinese fields come from `SelectionEntry.translations`.
- If a Chinese translation is missing, the English value is rendered on both
  sides as a transparent fallback.
- The overview block is optional and lists up to three renderable highlights
  chosen from the public Brief body, so every overview item appears below.
- Overview ranking is deterministic: mission/bridge items first, then
  `CompositeScore` descending, then Selection rank ascending.
- Mission/bridge means Simulation topic or bridge-shaped content such as world
  models, digital physics, simulation evals, synthetic worlds, consciousness
  modeling, or epistemic simulation.
- Each entry uses paired bilingual lines joined by ` ｜ `.
- Entry blocks are separated by `---`.
- KOL roster is optional. It appears only when selected Items have `kol:*`
  markers in `topics_raw`, ordered by first appearance in Selection rank order.
- Missing corpus Items are skipped rather than fabricated.
