/**
 * Markdown parsing utilities for extracting and processing weekly gist content.
 */

/**
 * Extracts the Weekly Brief section from markdown content.
 * @param {string} md - The markdown content to parse
 * @returns {string[]|null} Array of lines in the brief section, or null if not found
 */
export function extractBrief(md) {
  const lines = md.split(/\r?\n/);
  // Find start: H2 weekly brief header OR any line containing 'weekly brief' (bold or plain)
  let startIdx = lines.findIndex((l) => /^\s*##\s+.*weekly\s+brief.*$/i.test(l.trim()));
  if (startIdx < 0) {
    startIdx = lines.findIndex((l) => /\bweekly\s+brief\b/i.test(l));
  }
  if (startIdx < 0) return null;
  // Find end: next major section header (bold A/B/C) or next H2 that is not weekly brief
  let endIdx = lines.length;
  for (let i = startIdx + 1; i < lines.length; i++) {
    const t = lines[i].trim();
    if (/^\s*##\s+/.test(t) && !/weekly\s+brief/i.test(t)) { endIdx = i; break; }
    if (/^\s*\*\*[A-Z]\)\s+/.test(t)) { endIdx = i; break; }
  }
  return lines.slice(startIdx, endIdx);
}

/**
 * Removes the Weekly Brief header line from an array of lines.
 * @param {string[]} lines - Array of markdown lines
 * @returns {string[]} Lines without the header
 */
export function removeWeeklyBriefHeader(lines) {
  // Drop any line that looks like the Weekly Brief header
  const out = lines.filter((l) => !/^\s*##\s+.*weekly\s+brief.*$/mi.test(l));
  // Remove leading blank lines if present
  while (out.length && out[0].trim() === "") out.shift();
  return out;
}

/**
 * Extracts the Top Items section from lines.
 * @param {string[]} lines - Array of markdown lines
 * @returns {string[]} Lines in the Top Items section
 */
export function extractTopItemsSection(lines) {
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

/**
 * Extracts the title segment from a heading text (part before date separator).
 * @param {string} headingText - The heading text to parse
 * @returns {string} The title segment
 */
export function extractTitleSegment(headingText) {
  // Extract the part before the date separator "— YYYY-MM-DD —" if present
  const m = headingText.match(/^(.*?)\s+—\s+\d{4}-\d{2}-\d{2}\s+—\s+\[.*?\]/);
  if (m) return m[1].trim();
  const idx = headingText.indexOf("—");
  if (idx > 0) return headingText.slice(0, idx).trim();
  return headingText.trim();
}

/**
 * Parses metadata (type, date, URL) from a heading text.
 * @param {string} headingText - The heading text to parse
 * @returns {{type: string, date: string, url: string}} Parsed metadata
 */
export function parseMetaFromHeading(headingText) {
  const s = headingText || "";
  const dateMatch = s.match(/\b(\d{4}-\d{2}-\d{2})\b/);
  const date = dateMatch ? dateMatch[1] : "";
  
  // Look for type in parentheses anywhere in the heading
  const typeMatch = s.match(/\(([^)]+)\)/);
  const type = typeMatch ? typeMatch[1] : "";
  
  const urlMatch = s.match(/\]\((https?:[^)]+)\)/);
  const url = urlMatch ? urlMatch[1] : "";
  return { type, date, url };
}

/**
 * Extracts composite score from a text string.
 * @param {string} s - Text that may contain a composite score
 * @returns {string} The composite score value, or empty string
 */
export function extractComposite(s) {
  if (!s) return "";
  const m = s.match(/^(\d+(?:\.\d+)?)/);
  return m ? m[1] : s.trim();
}

/**
 * Extracts topics from a text string.
 * @param {string} s - Text that may contain topics
 * @returns {string} The topics, or empty string
 */
export function extractTopics(s) {
  if (!s) return "";
  const m = s.match(/Topics:\s*(.+)$/i);
  return m ? m[1].trim() : "";
}

/**
 * Parses items from brief lines into structured objects.
 * @param {string[]} lines - Array of markdown lines
 * @returns {Array<Object>} Array of parsed item objects
 */
export function parseItemsFromBrief(lines) {
  const items = [];
  let current = null;
  const topBullet = /^\s*(?:\*\*)?(?:\d+\.\s+|\*\s+)(.+—\s+\d{4}-\d{2}-\d{2}\s+—\s+\[.*?\].*)(?:\*\*)?\s*$/;
  const tldrRe = /^\s*\*\s*(?:\*{1,2}\s*)?TL;DR(?:\s*\*{1,2})?:\s*(.*)$/i;
  const ktRe = /^\s*\*\s*(?:\*{1,2}\s*)?(?:Key\s+Takeaways|Takeaways|Takeaway\s*\d+)(?:\s*\*{1,2})?:\s*(.*)$/i;
  const implRe = /^\s*\*\s*(?:\*{1,2}\s*)?Implication\s+for\s+Rex\s+Ren(?:\s*\([^)]*\))?(?:\s*\*{1,2})?:\s*(.*)$/i;
  const compRe = /^\s*\*\s*(?:\*{1,2}\s*)?CompositeScore(?:\s*[:(]\s*|\s+)(.*)$/i;

  for (const line of lines) {
    const t = line.trim();
    const mTop = line.match(topBullet);
    if (mTop) {
      if (current) items.push(current);
      const headingText = (mTop[1] || "").trim();
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
    if ((m = line.match(implRe))) { current.implicationText = (m[1] || "").trim(); current.hasImplication = true; continue; }
    if ((m = line.match(compRe))) { current.compositeText = (m[1] || "").trim(); current.hasComposite = true; continue; }
    // Preserve other lines as extras (English-only)
    if (t.length) current.extras.push(line);
  }
  if (current) items.push(current);
  return items;
}


