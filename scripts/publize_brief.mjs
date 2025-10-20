import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import dayjs from "dayjs";
import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";
// Load local env files first if present
dotenv.config({ path: path.resolve(process.cwd(), ".env.local"), override: true });
dotenv.config({ path: path.resolve(process.cwd(), ".env") });

const DIGEST_DIR = process.env.DIGEST_DIR || "Weekly_Gist";
const DIGEST_FILE = process.env.DIGEST_FILE || "";
const PUBLIC_DIR = process.env.PUBLIC_DIR || "Weekly_Gist/Public";
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
const TRANSFORM_MODE = process.env.TRANSFORM_MODE || "structured";
const PROMPT_PROFILE = process.env.PROMPT_PROFILE || "digest";
const PROMPT_FILE = process.env.PROMPT_FILE || "";

function resolvePromptPath() {
  if (PROMPT_FILE) return path.resolve(PROMPT_FILE);
  const candidates = [
    path.resolve(process.cwd(), "prompts", "generic_transform.md"),
    path.resolve(process.cwd(), "prompts", "generic_template.md"),
    path.resolve(process.cwd(), "templates", "generic_template.md"),
    path.resolve(
      process.cwd(),
      "prompts",
      PROMPT_PROFILE === "knowledge_card" ? "knowledge_card_transform.md" : "digest_transform.md"
    )
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return candidates[candidates.length - 1];
}

let PROMPT_TEXT = null;
try {
  const p = resolvePromptPath();
  if (fs.existsSync(p)) {
    PROMPT_TEXT = fs.readFileSync(p, "utf8");
    console.log("[publize] Loaded prompt from", p);
  }
} catch (e) {
  console.warn("[publize] Failed to load prompt file:", e?.message || e);
}

function findLatest(dir) {
  try {
    const abs = path.resolve(dir);
    const files = fs.readdirSync(abs).filter((n) => /^Weekly_Gist_\d{4}-\d{2}-\d{2}\.md$/.test(n));
    const sorted = files
      .map((name) => ({ name, full: path.join(abs, name), mtimeMs: fs.statSync(path.join(abs, name)).mtimeMs }))
      .sort((a, b) => b.mtimeMs - a.mtimeMs);
    return sorted[0]?.full || null;
  } catch {
    return null;
  }
}

function extractBrief(md) {
  const start = md.match(/^\s*##\s+.*weekly\s+brief.*$/mi);
  if (!start) return null;
  const i = start.index;
  const rest = md.slice(i + start[0].length);
  const next = rest.match(/^\s*##\s+\S+.*$/m);
  const end = next ? i + start[0].length + next.index : md.length;
  return md.slice(i, end).split(/\r?\n/);
}

function removeWeeklyBriefHeader(lines) {
  // Drop any line that looks like the Weekly Brief header
  const out = lines.filter((l) => !/^\s*##\s+.*weekly\s+brief.*$/mi.test(l));
  // Remove leading blank lines if present
  while (out.length && out[0].trim() === "") out.shift();
  return out;
}

function extractTopItemsSection(lines) {
  const headerRe = /^#{3,6}\s+Top\s+Items\s+for\s+Rex\s+Ren\b/i;
  const startIdx = lines.findIndex((l) => headerRe.test(l.trim()));
  if (startIdx < 0) return lines;
  let endIdx = lines.length;
  for (let i = startIdx + 1; i < lines.length; i++) {
    const t = lines[i].trim();
    if (/^#{2,6}\s+/.test(t) || /^---\s*$/.test(t)) { endIdx = i; break; }
  }
  return lines.slice(startIdx, endIdx);
}

function filterImplication(lines) {
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

async function translate(english) {
  if (!GEMINI_API_KEY) return null;
  try {
    const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({
      model: "gemini-2.5-flash",
      systemInstruction:
        "Translate each input line to Simplified Chinese, preserving Markdown. " +
        "Return JSON: {\"translations\":[{\"index\":0,\"zh\":\"...\"}, ...]}. Only JSON."
    });
    const payload = JSON.stringify({ input_lines: english });
    const res = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: payload }] }],
      generationConfig: { responseMimeType: "application/json", temperature: 0.2 }
    });
    const raw = res?.response?.text?.() ?? "";
    let data;
    try { data = JSON.parse(raw); } catch { data = JSON.parse(raw.replace(/^```json\s*|\s*```$/g, "")); }
    const zh = english.map((line, i) => {
      const item = Array.isArray(data?.translations) ? (data.translations.find((t) => t.index === i) ?? data.translations[i]) : null;
      return typeof item?.zh === "string" && item.zh.length ? item.zh : line;
    });
    return zh;
  } catch {
    return null;
  }
}

function build(english, chinese, src) {
  const date = src?.match(/Weekly_Gist_(\d{4}-\d{2}-\d{2})\.md$/)?.[1] || dayjs().format("YYYY-MM-DD");
  const header = [
    "# 本周 AI + Simulation | 博文精选",
    "",
    `> Date: ${date}`,
    ""
  ];

  // If translation is available, render Chinese-first pairs; else render English-only
  const pairs = [];
  if (Array.isArray(chinese)) {
    for (let i = 0; i < english.length; i++) {
      const en = english[i] ?? "";
      const zh = chinese[i] ?? "";
      const enTrim = en.trim();
      const zhTrim = zh.trim();
      if (enTrim === "" && zhTrim === "") {
        pairs.push("");
      } else {
        // Chinese first, then English
        if (zhTrim !== "") pairs.push(zh);
        if (enTrim !== "") pairs.push(en);
      }
    }
  } else {
    // No translation: publish English-only
    pairs.push(...english);
  }

  return { markdown: header.concat(pairs).join("\n"), date };
}

const PROMPT_SIGNAL_V4 = `---
 title: "Optimized SIGNAL Weekly Brief Transformation Prompt"
 version: v4.0
 author: Rex Ren
 layout: project-instruction
 ---
 
 # SIGNAL Weekly Brief Transformation Prompt（最终优化版）
 
 ## ROLE
 You are a **bilingual formatter-translator**.
 Convert internal Weekly Digest Markdown into **public, Xiaohongshu-ready bilingual blocks**.
 Do not rewrite; only **translate faithfully and reformat**.
 
 ---
 
 ## INPUT
 - **SOURCE_DIGEST_MD:** the original Markdown entry/entries containing
   - Title line
   - TL;DR
   - Takeaways bullets
   - Implication for Rex Ren
   - CompositeScore
   - Topics
   - Date
   - Type
   - URL
 
 ---
 
 ## INTRO SECTION
 At the top of the final output, always include a short bilingual intro before listing the entries.
 Use this structure:
 
 Title: 本周 AI + Simulation | 博文精选
 Date: {YYYY-MM-DD}
 
 **覆盖范围 Coverage window：** {YYYY-MM-DD} to {YYYY-MM-DD}
  **找到的项目 Items Found：** {N}
 
 简述：
 本周精选内容聚焦于「AI 代理体系」「模拟假说」「数字物理」「注意力经济」等关键主题，
 帮助读者快速捕捉智能体与模拟研究的前沿信号。
 Summary:
 This week’s digest focuses on AI agent systems, simulation theory, digital physics, and the attention economy—highlighting frontier signals in intelligent systems and simulated realities.
 
 Then list the bilingual entries formatted according to the TASK below.
 
 ⸻
 
 TASK
 
 For each entry, output ONE bilingual block, Chinese first, English second, line-by-line paired with a full-width bar “｜”.
 Use all fields if present. Only translation is allowed (no paraphrase).
 
 ⸻
 
 GLOBAL RULES
   • Translation = faithful, concise Simplified Chinese (简体中文).
   • Keep proper nouns (e.g., podcast names, product names) in English; add Chinese equivalents in parentheses only if commonly known.
   • Do not invent, omit, or rephrase information.
   • Keep English text exactly as in source (except renaming “Implication for Rex Ren” → “Implication”).
   • Use full-width bar with spaces: ” ｜ “ between ZH and EN on the same line.
   • Maintain all dates, types, and URLs.
   • Use em dashes “—” between title parts; middle dots “·” for inline separation if needed.
   • Preserve bullet count and order exactly as in the source.
   • Multiple entries separated by --- (three hyphens).
   • Add an emoji before each title based on Type: Podcast Episode=🎧, Blog Post=📝, Paper=📄, Talk=🎤, YouTube Video=📹; unknown type=⭐️.
   • Only include entries whose Date is within the coverage window (inclusive); remove items outside, and recompute Items Found accordingly.
   • No commentary, notes, or extra symbols beyond required fields.
 
 ⸻
 
 OUTPUT FORMAT (Markdown)
 
 Each entry follows this exact template:
 
 **标题｜Title**
  <emoji> <ZH translated title with type and date> ｜ <emoji> <EN original title with type and date>
  **来源｜Source**：<URL>
 
 **摘要｜TL;DR**
 <ZH translation of TL;DR> ｜ <Original EN TL;DR>
 
 **要点｜Takeaways**
 • <ZH translation of bullet 1> ｜ <Original EN bullet 1>
 • <ZH translation of bullet 2> ｜ <Original EN bullet 2>
 • <ZH translation of bullet 3> ｜ <Original EN bullet 3>
 (If the source has more bullets, continue pairing accordingly.)
 
 **启示｜Implication**
 <ZH translation of “Implication for Rex Ren”> ｜ <Original EN text, with heading normalized to “Implication”>
 
 **综合评分｜CompositeScore**
 <score number>
 
 **主题｜Topics**
 <ZH translations, comma-separated> ｜ <Original EN topics, comma-separated>
 
 ⸻
 
 QUALITY CHECK
 
 Before finalizing:
   1. “Implication for Rex Ren” must be renamed to “Implication.”
   2. No paraphrasing — English remains verbatim, Chinese strictly faithful.
   3. Each bullet in EN has a 1:1 Chinese pair on the same line.
   4. Each bilingual line joined with “ ｜ ”, no half-width pipes.
   5. Correct use of parentheses for type translation:
   • (Podcast Episode) → （播客集）
   • (Blog Post) → （博客）
   • (Paper) → （论文）
   • (Talk) → （演讲）
   • (YouTube Video) → （视频）
   6. The output reads fluently in both languages and is visually ready for publication on Xiaohongshu.
 
 ⸻
 
 BATCH PROCESSING
 
 When processing multiple entries:
   • Keep them in the same chronological order as the source.
   • Separate each entry with --- (three hyphens on its own line).
   • Do not repeat the intro section; include it once at the top.
 
 ⸻
 
 OBJECTIVE
 
 Output must be publication-ready bilingual markdown, preserving every original fact while translating faithfully for clarity, tone, and aesthetics suitable for Xiaohongshu’s intellectual audience.
`;

async function transformWithPrompt(sourceMd, src) {
  const date = src?.match(/Weekly_Gist_(\d{4}-\d{2}-\d{2})\.md$/)?.[1] || dayjs().format("YYYY-MM-DD");
  if (!GEMINI_API_KEY) {
    console.warn("[publize] Prompt mode requested but GEMINI_API_KEY missing; falling back to English-only.");
    return { markdown: sourceMd, date };
  }
  try {
    const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    const promptPrimer = PROMPT_TEXT || PROMPT_SIGNAL_V4;
    const augmented = `${promptPrimer}\n\nDate: ${date}\n\nSOURCE_DIGEST_MD\n\n${sourceMd}`;
    const res = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: augmented }] }],
      generationConfig: { responseMimeType: "text/plain", temperature: 0 }
    });
    let md = res?.response?.text?.() ?? "";
    // Strip surrounding fences if present
    md = md.replace(/^```\w*\n/, "").replace(/\n```\s*$/, "");
    return { markdown: md, date };
  } catch (err) {
    console.warn("[publize] Prompt transform failed; using source digest text. Error:", err?.message || err);
    return { markdown: sourceMd, date };
  }
}

async function main() {
  let src = null;
  if (DIGEST_FILE) {
    const c = path.resolve(DIGEST_FILE);
    if (fs.existsSync(c) && c.endsWith(".md")) src = c;
  }
  if (!src) src = findLatest(DIGEST_DIR);
  if (!src) { setOutputs({ public_file: "", digest_date: dayjs().format("YYYY-MM-DD") }); return; }
  const md = fs.readFileSync(src, "utf8");
  const brief = extractBrief(md);
  if (!brief || !brief.length) { setOutputs({ public_file: "", digest_date: dayjs().format("YYYY-MM-DD") }); return; }

  let markdown, date;

  if (TRANSFORM_MODE === "prompt") {
    console.log("[publize] Using prompt-driven transformation mode");
    const noHeader = removeWeeklyBriefHeader(brief);
    const coverageLine = brief.find((l) => /\*\*COVERAGE_WINDOW:/i.test(l));
    const topSection = extractTopItemsSection(noHeader);

    // Parse and preselect Top 5 items by CompositeScore
    const items = parseItemsFromBrief(topSection);
    items.sort((a, b) => parseFloat(b.compositeText) - parseFloat(a.compositeText));
    const top5 = items.slice(0, 5);

    // Build source MD for prompt: CN coverage + intro-only aggregator + preselected items
    const formatCnDate = (s) => {
      const m = s?.match(/^(\d{4})-(\d{2})-(\d{2})$/);
      return m ? `${m[1]}年${m[2]}月${m[3]}日` : s || "";
    };
    let coverageCnLine = "";
    if (coverageLine) {
      const m = coverageLine.match(/(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})/);
      if (m) coverageCnLine = `覆盖范围 Coverage window：**${formatCnDate(m[1])} 至 ${formatCnDate(m[2])}**`;
    }

    const srcLines = [];
    if (coverageLine) srcLines.push(coverageCnLine || coverageLine);
    // Aggregator only in intro
    srcLines.push("> 整理者：Rex Ren");
    srcLines.push("");

    // Reconstruct Top Items section in ranking order for clarity
    srcLines.push("### Top Items (Preselected by CompositeScore)");
    for (let i = 0; i < top5.length; i++) {
      const it = top5[i];
      const headingContent = it.headingLine.replace(/^\s*\d+\.\s+/, "").trim();
      srcLines.push(`${i + 1}. ${headingContent}`);
      if (it.hasTLDR) srcLines.push(`* **TL;DR:** ${it.tldrText}`);
      if (it.hasTakeaways) srcLines.push(`* **Key Takeaways:** ${it.takeawaysText}`);
      if (it.hasComposite) srcLines.push(`* **CompositeScore:** ${it.compositeText}`);
      srcLines.push("");
    }

    const srcMd = srcLines.join("\n");
    ({ markdown, date } = await transformWithPrompt(srcMd, src));

    // Post-process to enforce aggregator formatting and CN coverage window in output
    const enforceAggregatorBlockquote = (md) => {
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
    };
    const enforceCnCoverageWindow = (md) => {
      const fmt = (s) => {
        const m = s?.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        return m ? `${m[1]}年${m[2]}月${m[3]}日` : s || "";
      };
      return md.replace(
        /(\*\*)?覆盖范围 Coverage window：(\*\*)?\s*(\d{4}-\d{2}-\d{2})\s*[—\-]\s*(\d{4}-\d{2}-\d{2})/,
        (m0, s1, s2, d1, d2) => `覆盖范围 Coverage window：**${fmt(d1)} 至 ${fmt(d2)}**`
      );
    };
    function insertSeparatorBetweenOverviewAndFirstItem(md) {
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
    function stripTrailingSeparators(md) {
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
    markdown = enforceAggregatorBlockquote(markdown);
    markdown = enforceCnCoverageWindow(markdown);
    markdown = insertSeparatorBetweenOverviewAndFirstItem(markdown);
    markdown = stripTrailingSeparators(markdown);
  } else {
    const englishBase = filterImplication(brief);
    const english = removeWeeklyBriefHeader(englishBase);
    const items = parseItemsFromBrief(english);
    console.log(`[publize] parsed items: ${items.length}`);
    const zhMap = await translateStructured(items);
    ({ markdown, date } = buildStructured(items, zhMap, src));
    // also strip trailing separators for structured mode, just in case
    markdown = stripTrailingSeparators(markdown);
  }

  const outDir = ensureDir(PUBLIC_DIR);
  const outPath = path.join(outDir, `Weekly_Brief_Public_${date}.md`);
  fs.writeFileSync(outPath, markdown, "utf8");
  setOutputs({ public_file: outPath, digest_date: date });
}

function ensureDir(d) { const abs = path.resolve(d); if (!fs.existsSync(abs)) fs.mkdirSync(abs, { recursive: true }); return abs; }
function setOutputs(o) {
  const f = process.env.GITHUB_OUTPUT; if (!f) return;
  fs.appendFileSync(f, Object.entries(o).map(([k,v]) => `${k}=${v}`).join("\n") + "\n");
}

main();


function extractTitleSegment(headingText) {
  // Extract the part before the date separator "— YYYY-MM-DD —" if present
  const m = headingText.match(/^(.*?)\s+—\s+\d{4}-\d{2}-\d{2}\s+—\s+\[.*?\]/);
  if (m) return m[1].trim();
  const idx = headingText.indexOf("—");
  if (idx > 0) return headingText.slice(0, idx).trim();
  return headingText.trim();
}

function parseItemsFromBrief(lines) {
  const items = [];
  let current = null;
  const topBullet = /^\s*\d+\.\s+\*\*(.+?)\*\*\s*$/;
  const tldrRe = /^\s*\*\s+\*\*TL;DR:\*\*\s*(.*)$/i;
  const ktRe = /^\s*\*\s+\*\*(?:Key\s+Takeaways|Takeaways):\*\*\s*(.*)$/i;
  const compRe = /^\s*\*\s+\*\*CompositeScore:\*\*\s*(.*)$/i;

  for (const line of lines) {
    const t = line.trim();
    const mTop = line.match(topBullet);
    if (mTop) {
      if (current) items.push(current);
      const headingText = mTop[1];
      current = {
        headingLine: line,
        headingText,
        titleText: extractTitleSegment(headingText),
        tldrText: "",
        takeawaysText: "",
        compositeText: "",
        hasTLDR: false,
        hasTakeaways: false,
        hasComposite: false,
        extras: []
      };
      continue;
    }
    if (!current) continue;
    let m;
    if ((m = line.match(tldrRe))) { current.tldrText = (m[1] || "").trim(); current.hasTLDR = true; continue; }
    if ((m = line.match(ktRe))) { current.takeawaysText = (m[1] || "").trim(); current.hasTakeaways = true; continue; }
    if ((m = line.match(compRe))) { current.compositeText = (m[1] || "").trim(); current.hasComposite = true; continue; }
    // Preserve other lines as extras (English-only)
    if (t.length) current.extras.push(line);
  }
  if (current) items.push(current);
  return items;
}

async function translateStructured(items) {
  if (!GEMINI_API_KEY) return null;
  try {
    const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({
      model: "gemini-2.5-flash",
      systemInstruction:
        "Translate provided fields to Simplified Chinese, preserving Markdown and numbers. " +
        "Return JSON: {\"translations\":[{\"index\":0,\"titleZh\":\"...\",\"tldrZh\":\"...\",\"takeawaysZh\":\"...\",\"compositeZh\":\"...\"}, ...]}. Only JSON."
    });
    const payload = {
      items: items.map((it, index) => ({ index, title: it.titleText, tldr: it.tldrText, takeaways: it.takeawaysText, composite: it.compositeText }))
    };
    const res = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: JSON.stringify(payload) }] }],
      generationConfig: { responseMimeType: "application/json", temperature: 0.2 }
    });
    const raw = res?.response?.text?.() ?? "";
    let data;
    try { data = JSON.parse(raw); } catch { data = JSON.parse(raw.replace(/^```json\s*|\s*```$/g, "")); }
    const map = new Map();
    const arr = Array.isArray(data?.translations) ? data.translations : [];
    for (const item of arr) map.set(item.index, item);
    return map;
  } catch {
    return null;
  }
}

function buildStructured(items, zhMap, src) {
  const date = src?.match(/Weekly_Gist_(\d{4}-\d{2}-\d{2})\.md$/)?.[1] || dayjs().format("YYYY-MM-DD");
  const out = ["# \u672c\u5468 AI + Simulation | \u535a\u6587\u7cbe\u9009", "", `> Date: ${date}`, ""]; // Title in Chinese

  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const zh = zhMap ? zhMap.get(i) : null;
    const titleZh = (zh?.titleZh || it.titleText).trim();
    const tldrZh = (zh?.tldrZh || it.tldrText).trim();
    const takeZh = (zh?.takeawaysZh || it.takeawaysText).trim();
    const compZh = (zh?.compositeZh || it.compositeText).trim();

    console.log(`[publize] fields for #${i+1}: title=${it.titleText.length} tldr=${it.tldrText.length} take=${it.takeawaysText.length} comp=${it.compositeText.length}`);

    // One bullet for the item; Chinese title first, then English heading on next indented line
    out.push(`*   **${titleZh}**`);
    const englishHeadingContent = it.headingLine.replace(/^\s*\*\s+/, "").trim();
    out.push(`    ${englishHeadingContent}`);

    // Bilingual labeled sub-lines on the same line (nested bullets)
    if (it.hasTLDR) {
      const joined = `${tldrZh || it.tldrText}${it.tldrText ? ` ${it.tldrText}` : ""}`.trim();
      out.push(`    *   要点/TL;DR: ${joined}`);
    }
    if (it.hasTakeaways) {
      const joined = `${takeZh || it.takeawaysText}${it.takeawaysText ? ` ${it.takeawaysText}` : ""}`.trim();
      out.push(`    *   主要观点/Key Takeaways: ${joined}`);
    }
    if (it.hasComposite) {
      const joined = `${compZh || it.compositeText}${it.compositeText ? ` ${it.compositeText}` : ""}`.trim();
      out.push(`    *   综合评分/CompositeScore: ${joined}`);
    }

    // Preserve any extra English-only lines under this bullet
    for (const ex of it.extras) {
      out.push(`    ${ex.replace(/^\s*/, "").replace(/^\*\s*/, "* ")}`);
    }

    out.push("");
  }

  return { markdown: out.join("\n"), date };
}