/**
 * Transform markdown files to strict template format.
 */

import fs from "node:fs";
import path from "node:path";
import {
  parseMarkdown,
  findSection,
  extractSectionContent,
  splitIntoItems,
  extractBilingual,
  normalizeToStrict
} from "./markdown_utils.mjs";

/**
 * Transforms a Weekly Brief Public file to strict template format.
 * @param {string} content - Original markdown content
 * @param {string} filename - Source filename for date extraction
 * @returns {string} Transformed content
 */
export function transformWeeklyBriefPublic(content, filename) {
  const lines = content.split(/\r?\n/);
  const output = [];

  // Extract date from filename
  const dateMatch = filename.match(/(\d{4}-\d{2}-\d{2})/);
  const date = dateMatch ? dateMatch[1] : "";

  // Parse structure
  const structure = parseMarkdown(content);

  // Build title
  const title = structure.title || `Weekly Digest – ${date}`;
  output.push(`# ${title}`);
  output.push("");

  // Author (required)
  const author = structure.author || "> 整理者：Rex Ren";
  output.push(author);
  output.push("");

  // Optional coverage window if in intro
  if (structure.intro.length > 0) {
    const introText = structure.intro.join("\n");
    if (introText.includes("Coverage") || introText.includes("coverage")) {
      output.push(...structure.intro.filter(l => l.trim()));
      output.push("");
    }
  }

  // Section delimiter
  output.push("---");
  output.push("");

  // Transform items - split by --- delimiters after the first one
  let itemNumber = 1;
  
  // Get all content after first delimiter
  const firstDelimiterIdx = lines.findIndex(l => /^---+$/.test(l.trim()));
  if (firstDelimiterIdx < 0) {
    // No items to transform
    return output.join("\n");
  }

  // Split content into items by --- delimiters
  const itemBlocks = [];
  let currentBlock = [];
  
  for (let i = firstDelimiterIdx + 1; i < lines.length; i++) {
    const line = lines[i];
    if (/^---+$/.test(line.trim())) {
      if (currentBlock.length > 0) {
        itemBlocks.push([...currentBlock]);
        currentBlock = [];
      }
    } else {
      currentBlock.push(line);
    }
  }
  if (currentBlock.length > 0) {
    itemBlocks.push(currentBlock);
  }

  // Transform each item block
  for (const block of itemBlocks) {
    const itemContent = block.join("\n");
    const itemData = parseWeeklyBriefItem(itemContent);

    if (itemData && (itemData.titleCn || itemData.titleEn)) {
      // Build item title
      const titleCn = itemData.titleCn || itemData.titleEn || "";
      const titleEn = itemData.titleEn || itemData.titleCn || "";
      output.push(`## Item ${itemNumber}｜${titleCn} / ${titleEn}`);
      output.push("");

      output.push("**中文**");
      
      if (itemData.titleCn) {
        output.push(`标题：${itemData.titleCn}`);
      }
      if (itemData.sourceCn) {
        output.push(`来源：${itemData.sourceCn}`);
      }
      if (itemData.summaryCn) {
        output.push(`摘要：${itemData.summaryCn}`);
      }
      if (itemData.takeawaysCn) {
        output.push(`要点：${itemData.takeawaysCn}`);
      }
      if (itemData.implicationCn) {
        output.push(`启示：${itemData.implicationCn}`);
      }
      if (itemData.score !== null && itemData.score !== undefined) {
        output.push(`评分：${itemData.score}`);
      }
      if (itemData.topicsCn) {
        output.push(`主题：${itemData.topicsCn}`);
      }

      output.push("");
      output.push("**English**");
      
      if (itemData.titleEn) {
        output.push(`Title: ${itemData.titleEn}`);
      }
      if (itemData.sourceEn) {
        output.push(`Source: ${itemData.sourceEn}`);
      }
      if (itemData.summaryEn) {
        output.push(`TL;DR: ${itemData.summaryEn}`);
      }
      if (itemData.takeawaysEn) {
        output.push(`Takeaways: ${itemData.takeawaysEn}`);
      }
      if (itemData.implicationEn) {
        output.push(`Implication: ${itemData.implicationEn}`);
      }
      if (itemData.score !== null && itemData.score !== undefined) {
        output.push(`CompositeScore: ${itemData.score}`);
      }
      if (itemData.topicsEn) {
        output.push(`Topics: ${itemData.topicsEn}`);
      }

      output.push("");
      output.push("---");
      output.push("");

      itemNumber++;
    }
  }

  return output.join("\n");
}

/**
 * Parses a weekly brief item from markdown content.
 * @param {string} content - Item markdown content
 * @returns {Object|null} Parsed item data
 */
function parseWeeklyBriefItem(content) {
  const lines = content.split(/\r?\n/);
  const item = {
    titleCn: null,
    titleEn: null,
    sourceCn: null,
    sourceEn: null,
    summaryCn: null,
    summaryEn: null,
    takeawaysCn: null,
    takeawaysEn: null,
    implicationCn: null,
    implicationEn: null,
    score: null,
    topicsCn: null,
    topicsEn: null
  };

  let i = 0;
  while (i < lines.length) {
    const line = lines[i].trim();
    
    // Skip empty lines and separators
    if (!line || /^---+$/.test(line)) {
      i++;
      continue;
    }

    // Title field: **标题｜Title** on one line, content on next
    if (/^\*\*标题[｜|]Title\*\*/.test(line)) {
      if (i + 1 < lines.length) {
        const titleLine = lines[i + 1].trim();
        const bilingual = extractBilingual(titleLine);
        if (bilingual) {
          // Clean up emoji and parenthetical info
          item.titleCn = bilingual.cn.replace(/⭐️\s*/, "").replace(/\s*（[^）]+）\s*$/, "").trim();
          item.titleEn = bilingual.en.replace(/⭐️\s*/, "").replace(/\s*\([^)]+\)\s*$/, "").trim();
        } else {
          // Not bilingual, use same for both
          const cleaned = titleLine.replace(/⭐️\s*/, "").trim();
          item.titleCn = cleaned;
          item.titleEn = cleaned;
        }
        i += 2;
        continue;
      }
    }

    // Source field: **来源｜Source**：URL (on same line)
    if (/^\*\*来源[｜|]Source\*\*/.test(line)) {
      const match = line.match(/：\s*(.+)/) || line.match(/:\s*(.+)/);
      if (match) {
        const url = match[1].trim();
        item.sourceCn = url;
        item.sourceEn = url;
      }
      i++;
      continue;
    }

    // Summary field: **摘要｜TL;DR** on one line, content on next
    if (/^\*\*摘要[｜|]TL;DR\*\*/.test(line)) {
      if (i + 1 < lines.length) {
        const summaryLine = lines[i + 1].trim();
        const bilingual = extractBilingual(summaryLine);
        if (bilingual) {
          item.summaryCn = bilingual.cn.trim();
          item.summaryEn = bilingual.en.trim();
        } else {
          item.summaryCn = summaryLine;
          item.summaryEn = summaryLine;
        }
        i += 2;
        continue;
      }
    }

    // Takeaways field: **要点｜Takeaways** on one line, content on next
    if (/^\*\*要点[｜|]Takeaways\*\*/.test(line)) {
      if (i + 1 < lines.length) {
        const takeawaysLine = lines[i + 1].trim();
        const bilingual = extractBilingual(takeawaysLine);
        if (bilingual) {
          item.takeawaysCn = bilingual.cn.trim();
          item.takeawaysEn = bilingual.en.trim();
        } else {
          item.takeawaysCn = takeawaysLine;
          item.takeawaysEn = takeawaysLine;
        }
        i += 2;
        continue;
      }
    }

    // Implication field: **启示｜Implication** on one line, content on next
    if (/^\*\*启示[｜|]Implication\*\*/.test(line)) {
      if (i + 1 < lines.length) {
        const implicationLine = lines[i + 1].trim();
        const bilingual = extractBilingual(implicationLine);
        if (bilingual) {
          item.implicationCn = bilingual.cn.trim();
          item.implicationEn = bilingual.en.trim();
        } else {
          item.implicationCn = implicationLine;
          item.implicationEn = implicationLine;
        }
        i += 2;
        continue;
      }
    }

    // Score field: **综合评分｜CompositeScore** (number on same or next line)
    if (/^\*\*综合评分[｜|]CompositeScore\*\*/.test(line)) {
      const match = line.match(/\*\*[^*]+\*\*\s*(\d+\.?\d*)/);
      if (match) {
        item.score = match[1];
      } else if (i + 1 < lines.length) {
        const scoreLine = lines[i + 1].trim();
        const scoreMatch = scoreLine.match(/(\d+\.?\d*)/);
        if (scoreMatch) {
          item.score = scoreMatch[1];
          i += 2;
          continue;
        }
      }
      i++;
      continue;
    }

    // Topics field: **主题｜Topics** on one line, content on next
    if (/^\*\*主题[｜|]Topics\*\*/.test(line)) {
      if (i + 1 < lines.length) {
        const topicsLine = lines[i + 1].trim();
        const bilingual = extractBilingual(topicsLine);
        if (bilingual) {
          item.topicsCn = bilingual.cn.trim();
          item.topicsEn = bilingual.en.trim();
        } else {
          item.topicsCn = topicsLine;
          item.topicsEn = topicsLine;
        }
        i += 2;
        continue;
      }
    }

    i++;
  }

  // Return item if at least title or summary exists
  return (item.titleCn || item.titleEn || item.summaryCn || item.summaryEn) ? item : null;
}

/**
 * Whether a trimmed line is a Section C (PER-ITEM BLOG NOTES) heading.
 * Matches #/##/###, bold **...**, optional "C)" prefix, optional suffix after NOTES.
 * @param {string} trimmed - Single line, trimmed
 * @returns {boolean}
 */
export function isPerItemBlogNotesHeader(trimmed) {
  if (!trimmed) return false;
  if (/^#{1,3}\s*(?:C[\)）]\s*)?PER-ITEM\s+BLOG\s+NOTES\b/i.test(trimmed)) return true;
  if (
    /^\*\*(?:C[\)）]\s*)?PER-ITEM\s+BLOG\s+NOTES\b/i.test(trimmed) &&
    /\*\*\s*$/.test(trimmed)
  ) {
    return true;
  }
  return false;
}

/**
 * Transforms a Weekly Gist file to strict template format.
 * Focuses on Section C (PER-ITEM BLOG NOTES) normalization.
 * @param {string} content - Original markdown content
 * @param {string} filename - Source filename
 * @returns {string} Transformed content
 */
export function transformWeeklyGist(content, filename) {
  const output = [];

  // Process sections - look for Section C in all content
  // Section C can be marked as "**C) PER-ITEM BLOG NOTES**" or "## PER-ITEM BLOG NOTES"
  const allLines = content.split(/\r?\n/);
  let inSectionC = false;
  let sectionCStartIdx = -1;
  let sectionCEndIdx = -1;

  // Find Section C boundaries
  for (let i = 0; i < allLines.length; i++) {
    const line = allLines[i].trim();

    // Detect Section C header (many legacy variants → normalized later)
    if (isPerItemBlogNotesHeader(line) && !inSectionC) {
      inSectionC = true;
      sectionCStartIdx = i;
      continue;
    }

    // Detect end of Section C (next major section or end of file)
    if (inSectionC) {
      // Lettered block **D) ...**, or top-level ## heading that is not PER-ITEM.
      // Use ^##\s+ only (not ###) so ## subtitles inside an item do not end Section C.
      if (
        /^\*\*[A-Z][\)）]\s+/.test(line) ||
        (/^##\s+/.test(line) && !isPerItemBlogNotesHeader(line))
      ) {
        sectionCEndIdx = i;
        break;
      }
    }
  }

  if (sectionCEndIdx === -1 && inSectionC) {
    sectionCEndIdx = allLines.length;
  }

  // Process content
  if (sectionCStartIdx >= 0) {
    // Output content before Section C (sections A and B)
    if (sectionCStartIdx > 0) {
      const beforeSectionC = allLines.slice(0, sectionCStartIdx);
      output.push(...beforeSectionC);
      output.push("");
    }

    // Output Section C header
    output.push("## PER-ITEM BLOG NOTES");
    output.push("");

    // Extract and transform Section C items
    const sectionCLines = allLines.slice(sectionCStartIdx + 1, sectionCEndIdx);
    const blogItems = extractBlogItemsFromSectionC(sectionCLines);

    // Output each blog item in strict format
    for (const item of blogItems) {
      output.push(...item);
      output.push("");
    }

    // Output remaining content after Section C (if any)
    if (sectionCEndIdx < allLines.length) {
      output.push("");
      output.push(...allLines.slice(sectionCEndIdx));
    }
  } else {
    // Section C not found, return content as-is
    return content;
  }

  return output.join("\n");
}

/**
 * Extracts and transforms blog items from Section C content.
 * @param {string[]} lines - Section C lines
 * @returns {Array<string[]>} Array of transformed blog item lines (first element may be intro text)
 */
function extractBlogItemsFromSectionC(lines) {
  const items = [];
  let currentLines = [];
  let introLines = [];
  let foundFirstItem = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Detect blog item start: H1 header
    if (/^#\s+/.test(trimmed)) {
      if (!foundFirstItem) {
        // Save any intro lines before first item
        if (introLines.length > 0) {
          items.push(introLines);
        }
        foundFirstItem = true;
      } else if (currentLines.length > 0) {
        // Save previous item
        items.push(normalizeBlogItem(currentLines));
      }
      // Start new item
      currentLines = [line];
      continue;
    }

    if (foundFirstItem) {
      // Add line to current item
      currentLines.push(line);
    } else {
      // Collect intro lines before first item
      introLines.push(line);
    }
  }

  // Finalize last item
  if (currentLines.length > 0) {
    items.push(normalizeBlogItem(currentLines));
  }

  return items;
}

/**
 * Normalizes a blog item to strict template format.
 * @param {string[]} lines - Blog item content lines
 * @returns {string[]} Normalized blog item lines
 */
function normalizeBlogItem(lines) {
  // Blog items in Section C are typically already well-formatted
  // We just need to ensure they meet strict template requirements:
  // 1. H1 title
  // 2. Author line: > 整理者：Rex Ren
  // 3. Decorative line: ──────────────────────────────
  // 4. Resource section (optional)
  // 5. Sections with --- delimiters
  // 6. Sections with **中文** and **English** markers

  const output = [];
  let foundAuthor = false;
  let foundDecorative = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Ensure title is H1
    if (i === 0 && /^#\s+/.test(trimmed)) {
      output.push(line);
      output.push("");
      continue;
    }

    // Ensure author line format
    if (/>\s*整理者：/.test(trimmed)) {
      if (!trimmed.startsWith(">")) {
        output.push(`> ${trimmed.replace(/^>\s*/, "")}`);
      } else {
        output.push(line);
      }
      foundAuthor = true;
      output.push("");
      continue;
    }

    // Ensure decorative line format
    if (/^─+/.test(trimmed)) {
      if (!foundDecorative && foundAuthor) {
        output.push("──────────────────────────────");
        foundDecorative = true;
        output.push("");
        continue;
      }
    }

    // Keep all other lines as-is
    output.push(line);
  }

  return output;
}

/**
 * Checks if a file is already in strict format.
 * @param {string} content - File content
 * @returns {boolean} True if appears to be strict format
 */
export function isStrictFormat(content) {
  // Check for key strict format indicators:
  // 1. Author format: > 整理者：
  // 2. Section delimiter: ---
  // 3. Language markers: **中文** and **English**
  
  const hasAuthor = />\s*整理者：/.test(content);
  const hasDelimiter = /^---+$/m.test(content);
  const hasLanguageMarkers = /\*\*中文\*\*/.test(content) && /\*\*English\*\*/.test(content);

  return hasAuthor && hasDelimiter && hasLanguageMarkers;
}

