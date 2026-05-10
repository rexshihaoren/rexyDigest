import dayjs from "dayjs";
import { parseMetaFromHeading, extractComposite, extractTopics } from "./parser.mjs";

/**
 * Formatting and transformation utilities for markdown content.
 */

/**
 * Maps content type to emoji.
 * @param {string} type - Content type (e.g., "Podcast Episode", "Blog Post")
 * @returns {string} Emoji for the type
 */
export function mapTypeToEmoji(type) {
  const t = (type || "").toLowerCase();
  if (t.includes("podcast")) return "🎧";
  if (t.includes("blog")) return "📝";
  if (t.includes("paper") || t.includes("arxiv")) return "📄";
  if (t.includes("talk") || t.includes("lecture")) return "🎤";
  if (t.includes("youtube") || t.includes("video")) return "📹";
  return "⭐️";
}

/**
 * Translates content type to Chinese.
 * @param {string} type - Content type in English
 * @returns {string} Chinese translation of the type
 */
export function translateTypeCn(type) {
  const t = (type || "").toLowerCase();
  if (t.includes("podcast")) return "播客集";
  if (t.includes("blog")) return "博客";
  if (t.includes("paper") || t.includes("arxiv")) return "论文";
  if (t.includes("talk") || t.includes("lecture")) return "演讲";
  if (t.includes("youtube") || t.includes("video")) return "视频";
  return "未知类型";
}

/**
 * Filters out Implication for Rex Ren sections from lines.
 * @param {string[]} lines - Array of markdown lines
 * @returns {string[]} Lines without implication sections
 */
export function filterImplication(lines) {
  const header = /^#{2,6}\s+/;
  let drop = false;
  const out = [];
  for (const line of lines) {
    const t = line.trim();
    if (!drop && /^#{3,6}\s+Implication\s+for\s+Rex\s+Ren\b/i.test(t)) { drop = true; continue; }
    if (!drop && /Implication\s+for\s+Rex\s+Ren/i.test(t)) { continue; }
    if (drop && header.test(t)) { drop = false; out.push(line); continue; }
    if (!drop) out.push(line);
  }
  while (out.length && out[out.length - 1].trim() === "") out.pop();
  return out;
}

/**
 * Removes trailing separators (---) and blank lines from markdown.
 * @param {string} md - Markdown content
 * @returns {string} Cleaned markdown
 */
export function stripTrailingSeparators(md) {
  const lines = md.split(/\r?\n/);
  // remove trailing blank lines
  while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
  // remove trailing separators
  while (lines.length && lines[lines.length - 1].trim() === '---') {
    lines.pop();
    while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
  }
  return lines.join('\n');
}

/**
 * Enforces aggregator blockquote formatting in markdown.
 * @param {string} md - Markdown content
 * @returns {string} Markdown with normalized aggregator blockquote
 */
export function enforceAggregatorBlockquote(md) {
  const lines = md.split(/\r?\n/);
  let seen = false;
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^\s*>?\s*整理者：\s*Rex Ren\s*$/.test(l)) {
      if (!seen) {
        out.push("> 整理者：Rex Ren");
        seen = true;
      }
      // drop duplicates beyond intro
    } else {
      out.push(l);
    }
  }
  return out.join("\n");
}

/**
 * Formats a date string to Chinese format (YYYY年MM月DD日).
 * @param {string} s - Date string in YYYY-MM-DD format
 * @returns {string} Chinese formatted date
 */
function formatCnDate(s) {
  const m = s?.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${m[1]}年${m[2]}月${m[3]}日` : s || "";
}

/**
 * Enforces Chinese coverage window formatting in markdown.
 * @param {string} md - Markdown content
 * @returns {string} Markdown with normalized coverage window
 */
export function enforceCnCoverageWindow(md) {
  return md.replace(
    /(\*\*)?覆盖范围 Coverage window：(\*\*)?\s*(\d{4}-\d{2}-\d{2})\s*[—\-]\s*(\d{4}-\d{2}-\d{2})/,
    (m0, s1, s2, d1, d2) => `覆盖范围 Coverage window：**${formatCnDate(d1)} 至 ${formatCnDate(d2)}**`
  );
}

/**
 * Inserts a separator between overview section and first item.
 * @param {string} md - Markdown content
 * @returns {string} Markdown with separator inserted
 */
export function insertSeparatorBetweenOverviewAndFirstItem(md) {
  const lines = md.split(/\r?\n/);
  const idxTop = lines.findIndex((l) => /^\s*##\s+(?:🏅\s*)?Top\s*#\d+/.test(l));
  if (idxTop <= 0) return md;
  // find preceding non-empty line
  let j = idxTop - 1;
  while (j >= 0 && !lines[j].trim()) j--;
  if (j >= 0 && lines[j].trim() === '---') return md; // already has separator
  // ensure we are after Overview section; insert at idxTop
  lines.splice(idxTop, 0, '---');
  return lines.join('\n');
}

/**
 * Builds structured bilingual markdown from parsed items.
 * @param {Array<Object>} items - Parsed items from brief
 * @param {Map<number, Object>|null} zhMap - Translation map (index -> translations)
 * @param {string} src - Source file path
 * @returns {{markdown: string, date: string}} Formatted markdown and date
 */
export function buildStructured(items, zhMap, src) {
  const date = src?.match(/Weekly_Gist_(\d{4}-\d{2}-\d{2})\.md$/)?.[1] || dayjs().format("YYYY-MM-DD");
  const out = [
    `# Weekly Digest – ${date}`,
    "",
    `> 整理者：Rex Ren`,
    "",
    `---`,
    ""
  ];

  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const zh = zhMap ? zhMap.get(i) : null;
    const titleZh = (zh?.titleZh || it.titleText).trim();
    const tldrZh = (zh?.tldrZh || it.tldrText).trim();
    const takeZh = (zh?.takeawaysZh || it.takeawaysText).trim();
    const compZh = (zh?.compositeZh || it.compositeText).trim();

    console.log(`[publize] fields for #${i+1}: title=${it.titleText.length} tldr=${it.tldrText.length} take=${it.takeawaysText.length} comp=${it.compositeText.length}`);

    // Strict-template bilingual paired section
    const meta = parseMetaFromHeading(it.headingText);
    const emoji = mapTypeToEmoji(meta.type);
    const typeCn = translateTypeCn(meta.type);
    const compVal = extractComposite(it.compositeText);
    const topicsEn = extractTopics(it.compositeText);
    const topicsZhBase = zh?.topicsZh ?? topicsEn ?? "";
    const topicsZh = topicsZhBase.trim();
    const implZhBase = zh?.implicationZh ?? it.implicationText ?? "";
    const implZh = implZhBase.trim();

    out.push(`**标题｜Title**`);
    out.push(`${emoji} ${titleZh}（${typeCn}，${meta.date}） ｜ ${emoji} ${it.titleText} (${meta.type}, ${meta.date})`);
    if (meta.url) out.push(`**来源｜Source**：${meta.url}`);
    out.push("");

    if (it.hasTLDR) {
      out.push(`**摘要｜TL;DR**`);
      out.push(`${tldrZh} ｜ ${it.tldrText}`);
      out.push("");
    }

    if (it.hasTakeaways) {
      out.push(`**要点｜Takeaways**`);
      out.push(`• ${takeZh} ｜ ${it.takeawaysText}`);
      out.push("");
    }

    if (it.hasImplication) {
      out.push(`**启示｜Implication**`);
      out.push(`${implZh} ｜ ${it.implicationText}`);
      out.push("");
    }

    if (it.hasComposite) {
      out.push(`**综合评分｜CompositeScore**`);
      out.push(`${compVal}`);
      out.push("");
    }

    if (topicsEn) {
      out.push(`**主题｜Topics**`);
      out.push(`${topicsZh} ｜ ${topicsEn}`);
      out.push("");
    }

    out.push("---");
    out.push("");
  }

  return { markdown: out.join("\n"), date };
}


