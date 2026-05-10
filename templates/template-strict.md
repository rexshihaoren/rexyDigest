# Strict Template Specification

This document defines the mandatory structure for knowledge card input files.

## Overview

All input markdown files MUST follow this strict structure to ensure reliable parsing and generation.

## Required Structure

```markdown
# [REQUIRED] Main Title

## [OPTIONAL] Subtitle

[REQUIRED] Author line:
> 整理者：Author Name

[REQUIRED for non-weekly, OPTIONAL for weekly] Decorative separator:
──────────────────────────────

[OPTIONAL] Intro content
- URL is optional (especially for weekly summaries)
- Can include markdown formatting
- Everything until first section delimiter

---

## [REQUIRED] Section Title | Chinese / English

**中文**
[Chinese content here]

**English**
[English content here]

---

## [REQUIRED] Next Section Title

**中文**
[Content...]

**English**
[Content...]

---
```

## Field Specifications

### 1. Title (REQUIRED)
- **MUST** start with single `#` followed by space
- Example: `# My Project Title`
- **MUST** appear in first 10 lines
- Cannot use `Title:` prefix` format

### 2. Subtitle (OPTIONAL)
- If present, **MUST** start with `##` followed by space
- Example: `## Subtitle Here`
- Cannot be first line

### 3. Author (REQUIRED)
- **MUST** use exact format: `> 整理者：Author Name`
- Must appear before first `---` delimiter
- Alternative formats NOT supported in strict mode

### 4. Decorative Line (REQUIRED for non-weekly)
- Required for tutorial/course/workshop content
- Optional for weekly digest content
- Format: `──────────────────────────────`
- Must appear after author line
- Provides visual separation

### 5. Intro Content (OPTIONAL)
- URL is optional (no error if missing)
- Supports markdown formatting
- Continues until first `---` delimiter
- Can include:
  - Bullet points
  - URLs (optional)
  - Text content
  - Links

### 6. Section Delimiters (REQUIRED)
- **MUST** use `---` (three dashes) to separate sections
- At least one delimiter required
- Delimiter terminates intro, starts sections

### 7. Section Headers (REQUIRED)
- Each section **MUST** have header starting with `#`
- Can use `#`, `##`, or `###`
- First header in section becomes section title

### 8. Language Markers (RECOMMENDED)
- For bilingual content: `**中文**` and `**English**`
- Parser will issue warning if missing
- Not required for monolingual content

### 9. Visual Placeholders (OPTIONAL)
- Format: `(配图: path/to/image.png)`
- Supports:
  - Relative paths: `image.png`
  - URLs: `https://example.com/image.jpg`
  - Absolute paths: `/path/to/image.png`
  - Data URIs: `data:image/png;base64,...`

## Validation Checklist

Before generating cards, verify:

- [ ] Title starts with `# ` (single hash + space)
- [ ] Author uses format: `> 整理者：Author Name`
- [ ] At least one `---` delimiter exists
- [ ] Each section has header
- [ ] Language markers present (if bilingual)
- [ ] Visual placeholders use `(配图: ...)` format

## Examples

### Weekly Digest (No Decorative Line)

```markdown
# AI Simulation Weekly Digest

> 整理者：Rex Ren

Coverage: 2024-01-01 to 2024-01-07

---

## Item 1 | Chinese / English

**中文**
Content...

**English**
Content...
```

### Course Content (With Decorative Line)

```markdown
# ChatGPT Prompt Engineering

> 整理者：Rex Ren

──────────────────────────────

📍 Course URL
https://example.com/course

📚 Key Topics
• Topic 1
• Topic 2

---

## Step 1 | Chinese / English

**中文**
Content...

**English**
Content...
```

## Common Errors

### Title Errors
- ❌ `Title: Something` (missing `#`)
- ✅ `# Something`

### Author Errors
- ❌ `整理者：Name` (missing `>`)
- ❌ `by Author` (wrong format)
- ✅ `> 整理者：Author Name`

### Section Errors
- ❌ No `---` delimiters
- ❌ Missing section headers
- ✅ Proper structure with `---` and headers

## Enforcement

The parser will validate markdown before generation and display errors if structure doesn't match this specification.

See `docs/generic-template.md` for more flexible usage examples.


