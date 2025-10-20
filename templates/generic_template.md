# Flexible Knowledge Card Template

This is the **universal template** that works with the existing parsing logic in `cards_core.py`. It's compatible with all content types including `PEforDevs.md`, `NLPLabeling.md`, and can be adapted for any content.

## Flexible Template Structure

```markdown
# Your Project Title 项目标题

## Subtitle (optional)

# AUTHOR OPTIONS (choose one):
by Author Name
# OR
> Author Name  
# OR
> 整理者：Author Name
# OR
Author: Author Name

# URL OPTIONS (choose one):
https://example.com/url
# OR
<https://example.com/url>
# OR
# Skip URL entirely

# INTRO CONTENT (everything until first section becomes intro_cn):
📍 Resource Title
https://example.com/resource-url
Type: Video & Blog

📚 核心内容
• Key concept 1
• Key concept 2
• Key concept 3

### 核心看点 Overview（双语）
- 🏅 Top #1：Concept 1
- 🏅 Top #2：Concept 2

---

# SECTION OPTIONS (all work):
## Section Title｜中文 / English
## 🎯 Section Title｜中文 / English  
## 🏅 Top #1｜Title / English
### Subsection Title
# Main Section Title

# CONTENT STRUCTURE OPTIONS:

# Option 1: Simple
Chinese content...
- Point 1
- Point 2

---

English content...
- Point 1
- Point 2

# Option 2: With markers (ignored by parser)
**中文**

Chinese content...

**English**

English content...

# Option 3: Complex structure
### 📍 Resource
https://example.com/url

### 📚 核心内容
• Key point 1
• Key point 2

### 🎯 摘要 / TL;DR
Summary content...

---

English translation...

---

# Next section...
```

## Template Rules (FLEXIBLE REQUIREMENTS)

### 1. Cover Section (Required)
- **`# Title`** - Main title (required, must start with `#`)
- **`## Subtitle`** - Optional subtitle (must start with `##`)
- **Author line** - Choose one format:
  - `by Author Name` (traditional)
  - `> Author Name` (quote style)
  - `> 整理者：Author Name` (Chinese style)
  - `Author: Author Name` (label style)
- **URL line** - Optional (must start with `http://` or `https://`)
- **Intro content** - Everything until first section becomes intro_cn

### 2. Sections (Required)
- **Section headers** - Must start with `#` (any level works)
- **Content separation** - Use `---` to separate Chinese/English content
- **Content markers** - `**中文**` and `**English**` are optional (ignored by parser)

### 3. Content Guidelines (Flexible)
- Use bullet points (`•` or `-`)
- Include emojis for visual appeal (optional)
- Keep bilingual content parallel
- Use `![Image Description](url)` for images
- Place images in `assets/visuals/` directory

## Content Type Adaptations

### Course/Tutorial Content
```markdown
# Course Title 课程标题

> Course description and learning objectives
> 整理者：Rex Ren

──────────────────────────────

📍 Course Resource
https://example.com/course-url
Type: Course & Documentation

📚 核心内容
• Learning objective 1
• Learning objective 2
• Learning objective 3

---

## 🧩 Step 1｜中文标题 / English Title

**中文**
课程内容...

**English**
Course content...

---
```

### Workshop/Conference Content
```markdown
# Workshop Title 工作坊标题

> Workshop description and agenda
> 整理者：Rex Ren

──────────────────────────────

📍 Workshop Resources
https://example.com/workshop-url
Type: Workshop & Demo

📚 核心内容
• Workshop objective 1
• Workshop objective 2
• Workshop objective 3

---

## 🚧 Section 1｜中文标题 / English Title

![Image Description](https://example.com/image-url)

**中文**
工作坊内容...

**English**
Workshop content...

---
```

### Digest/Newsletter Content
```markdown
# Digest Title 精选标题

> Weekly digest description and coverage
> 整理者：Rex Ren

──────────────────────────────

📍 Digest Resources
https://example.com/digest-url
Type: Digest & Newsletter

📚 核心内容
• 覆盖范围：2025-01-01 to 2025-01-07
• 找到的项目：5
• 关键主题：主题1, 主题2, 主题3

---

## 📰 Item 1｜Resource Title 1 / Resource Title 1

**中文**

🎧 资源标题 — 中文描述（类型）— 2025-01-01
来源：https://example.com/resource-url

摘要：
中文摘要内容。

要点：
• 要点 1
• 要点 2
• 要点 3

启示：
中文启示内容。

综合评分：8.5
主题：主题1, 主题2

**English**

🎧 Resource Title — English Description (Type) — 2025-01-01
Source: https://example.com/resource-url

Summary:
English summary content.

Key Points:
• Key point 1
• Key point 2
• Key point 3

Implication:
English implication content.

Score: 8.5
Topics: Topic1, Topic2

---
```

### Research/Paper Content
```markdown
# Paper Title 论文标题

> Research paper summary and key findings
> 整理者：Rex Ren

──────────────────────────────

📍 Paper Resources
https://example.com/paper-url
Type: Research Paper & Code

📚 核心内容
• Research contribution 1
• Research contribution 2
• Research contribution 3

---

## 🔬 Method｜方法 / Methodology

**中文**
研究方法描述...

**English**
Methodology description...

---
```

### Product/Feature Content
```markdown
# Product Title 产品标题

> Product description and key features
> 整理者：Rex Ren

──────────────────────────────

📍 Product Resources
https://example.com/product-url
Type: Product & Documentation

📚 核心内容
• Feature 1
• Feature 2
• Feature 3

---

## ⚙️ Feature 1｜功能1 / Feature 1

**中文**
功能描述...

**English**
Feature description...

---
```

## Emoji Patterns by Content Type

- **Course/Tutorial**: `🧩` (Step), `⏳` (Time/Process)
- **Workshop/Conference**: `🚧` (Section), `💻` (Technical)
- **Digest/Newsletter**: `📰` (Item), `🎧` (Audio), `📝` (Article), `📹` (Video), `🎤` (Talk)
- **Research/Paper**: `🔬` (Method), `📊` (Results), `🧠` (Analysis)
- **Product/Feature**: `⚙️` (Feature), `🔧` (Tool), `🎯` (Goal)

## Examples

See these working examples:
- `input/PEforDevs.md` - Course content (follows template exactly)
- `input/NLPLabeling.md` - Workshop content (follows template exactly)
- `docs/WeeklyOct20-corrected.md` - Digest content (converted to template format)

## Usage

1. Copy the appropriate template above
2. Replace placeholder content with your actual content
3. Ensure you follow the **MUST FOLLOW** rules
4. Run: `INPUT_FILE=your-project.md ./run.sh`
5. Generated cards will appear in `output/your-project/cards/`
6. Generated PDF will appear in `output/your-project/pdfs/`

## Critical Notes

### What Works (Current Files)
- `PEforDevs.md` ✅ - Follows template exactly
- `NLPLabeling.md` ✅ - Follows template exactly

### What Doesn't Work (Needs Conversion)
- `WeeklyOct20.md` ❌ - Uses `Title:`, `Date:` instead of `# Title`
- Any file not following the **MUST FOLLOW** rules

### Conversion Required
If you have existing content that doesn't follow this template:
1. **Add proper cover section** with `# Title`, `> Author line`
2. **Convert items to sections** with `## Section Title｜中文 / English`
3. **Structure content** with `**中文**` and `**English**` markers
4. **Add `---` separators** between sections

This template is **100% compatible** with the existing parsing logic and will work for any content type!