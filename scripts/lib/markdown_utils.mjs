/**
 * Markdown parsing and manipulation utilities for strict template transformation.
 */

/**
 * Parses markdown into a structured representation.
 * @param {string} content - Markdown content
 * @returns {Object} Parsed structure with sections and metadata
 */
export function parseMarkdown(content) {
  const lines = content.split(/\r?\n/);
  const structure = {
    title: null,
    subtitle: null,
    author: null,
    decorativeLine: null,
    intro: [],
    sections: []
  };

  let currentSection = null;
  let inIntro = true;
  let introEnded = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Title detection (first H1 in first 10 lines)
    if (i < 10 && !structure.title && /^#\s+/.test(trimmed)) {
      structure.title = trimmed.replace(/^#+\s+/, "");
      continue;
    }

    // Subtitle detection (H2 before first ---)
    if (!introEnded && !structure.subtitle && /^##\s+/.test(trimmed)) {
      structure.subtitle = trimmed.replace(/^##+\s+/, "");
      continue;
    }

    // Author detection
    if (!introEnded && /^>\s*整理者：/.test(trimmed)) {
      structure.author = trimmed;
      continue;
    }

    // Decorative line detection
    if (!introEnded && /^────────────────+/.test(trimmed)) {
      structure.decorativeLine = trimmed;
      continue;
    }

    // Section delimiter detection
    if (/^---+$/.test(trimmed)) {
      if (inIntro) {
        introEnded = true;
        inIntro = false;
      } else if (currentSection) {
        currentSection.content.push(trimmed);
      }
      continue;
    }

    // Section header detection (## or ###)
    if (/^##+\s+/.test(trimmed)) {
      if (currentSection) {
        structure.sections.push(currentSection);
      }
      currentSection = {
        header: trimmed,
        level: (trimmed.match(/^#+/)?.[0] || "").length,
        content: [trimmed]
      };
      inIntro = false;
      continue;
    }

    // Content collection
    if (inIntro && !introEnded) {
      if (trimmed) {
        structure.intro.push(line);
      }
    } else if (currentSection) {
      currentSection.content.push(line);
    } else if (!introEnded) {
      structure.intro.push(line);
    }
  }

  if (currentSection) {
    structure.sections.push(currentSection);
  }

  return structure;
}

/**
 * Finds a section by header text (case-insensitive).
 * @param {Object} structure - Parsed markdown structure
 * @param {string|RegExp} pattern - Header text to match (string or regex)
 * @returns {Object|null} Section object or null
 */
export function findSection(structure, pattern) {
  const regex = typeof pattern === "string" 
    ? new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i")
    : pattern;

  return structure.sections.find(section => {
    const headerText = section.header.replace(/^#+\s+/, "").trim();
    return regex.test(headerText);
  }) || null;
}

/**
 * Extracts content between two sections.
 * @param {Object} structure - Parsed markdown structure
 * @param {string|RegExp} startPattern - Starting section pattern
 * @param {string|RegExp} endPattern - Ending section pattern (optional)
 * @returns {string[]} Array of content lines
 */
export function extractSectionContent(structure, startPattern, endPattern = null) {
  const startSection = findSection(structure, startPattern);
  if (!startSection) return [];

  const startIdx = structure.sections.indexOf(startSection);
  let endIdx = structure.sections.length;

  if (endPattern) {
    for (let i = startIdx + 1; i < structure.sections.length; i++) {
      const headerText = structure.sections[i].header.replace(/^#+\s+/, "").trim();
      const regex = typeof endPattern === "string"
        ? new RegExp(endPattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i")
        : endPattern;
      if (regex.test(headerText)) {
        endIdx = i;
        break;
      }
    }
  }

  const content = [];
  for (let i = startIdx; i < endIdx; i++) {
    content.push(...structure.sections[i].content);
  }

  return content;
}

/**
 * Splits content into items based on section headers or separators.
 * @param {string[]} lines - Content lines
 * @returns {Array<{header: string, content: string[]}>} Array of items
 */
export function splitIntoItems(lines) {
  const items = [];
  let currentItem = null;

  for (const line of lines) {
    const trimmed = line.trim();
    
    // Detect item headers: ## Item N, ## Item N｜, or ## with title
    if (/^##\s+Item\s+\d+/.test(trimmed) || 
        (/^##\s+/.test(trimmed) && trimmed.includes("｜")) ||
        (/^##\s+/.test(trimmed) && trimmed.includes("|"))) {
      if (currentItem) {
        items.push(currentItem);
      }
      currentItem = {
        header: trimmed,
        content: [trimmed]
      };
      continue;
    }

    // Detect H1 titles (for blog notes in Section C)
    if (/^#\s+/.test(trimmed) && trimmed !== lines[0]?.trim()) {
      if (currentItem) {
        items.push(currentItem);
      }
      currentItem = {
        header: trimmed,
        content: [trimmed]
      };
      continue;
    }

    // Detect section separators
    if (/^---+$/.test(trimmed)) {
      if (currentItem) {
        currentItem.content.push(trimmed);
        // Don't end on separator, continue collecting
      }
      continue;
    }

    if (currentItem) {
      currentItem.content.push(line);
    } else {
      // Content before first item
      if (!items.length) {
        items.push({ header: null, content: [line] });
        currentItem = items[0];
      } else {
        currentItem.content.push(line);
      }
    }
  }

  if (currentItem) {
    items.push(currentItem);
  }

  return items;
}

/**
 * Extracts bilingual content from a line or block.
 * @param {string} text - Text with potential bilingual separators (｜ or |)
 * @returns {Object} {cn: string, en: string} or null if not bilingual
 */
export function extractBilingual(text) {
  const separators = ["｜", "|"];
  for (const sep of separators) {
    if (text.includes(sep)) {
      const parts = text.split(sep).map(s => s.trim());
      if (parts.length >= 2) {
        return {
          cn: parts[0],
          en: parts[1]
        };
      }
    }
  }
  return null;
}

/**
 * Normalizes markdown structure to strict template format.
 * @param {Object} structure - Parsed structure
 * @param {Object} options - Transformation options
 * @returns {string} Transformed markdown
 */
export function normalizeToStrict(structure, options = {}) {
  const {
    isWeekly = false,
    preserveDecorativeLine = false
  } = options;

  const output = [];

  // Title (required)
  if (structure.title) {
    output.push(`# ${structure.title}`);
    output.push("");
  }

  // Subtitle (optional)
  if (structure.subtitle) {
    output.push(`## ${structure.subtitle}`);
    output.push("");
  }

  // Author (required)
  if (structure.author) {
    output.push(structure.author);
    output.push("");
  }

  // Decorative line (optional for weekly)
  if (structure.decorativeLine && (!isWeekly || preserveDecorativeLine)) {
    output.push(structure.decorativeLine);
    output.push("");
  }

  // Intro content
  if (structure.intro.length > 0) {
    output.push(...structure.intro.filter(l => l.trim()));
    output.push("");
  }

  // Section delimiter (required)
  output.push("---");
  output.push("");

  // Sections
  for (const section of structure.sections) {
    output.push(...section.content);
    output.push("");
  }

  return output.join("\n");
}


