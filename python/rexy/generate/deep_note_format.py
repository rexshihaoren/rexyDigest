"""Normalize and validate Rex-native KnowledgeCard deep-note Markdown."""

from __future__ import annotations

import re

DECORATIVE_SEPARATOR = "──────────────────────────────"

REQUIRED_SECTIONS = [
    "### 00｜为什么在意这篇",
    "### 01｜尝试回答的问题",
    "### 02｜创新点",
    "### 03｜与 AI X Simulation 的关系",
    "### 04｜关键论据",
    "### 05｜习惯性反思",
    "### 06｜沉淀一下",
    "### 参考文献",
]

REQUIRED_BULLETS = {
    "### 00｜为什么在意这篇": ["直觉", "它戳中的变化", "持续观察的方向"],
    "### 01｜尝试回答的问题": ["长期问题", "急迫性", "切入点"],
    "### 02｜创新点": ["关键论点", "为什么成立"],
    "### 03｜与 AI X Simulation 的关系": ["连接点", "重要性", "还差一步"],
    "### 04｜关键论据": ["支撑材料", "最可信的点", "可被challenge"],
    "### 05｜习惯性反思": ["还没说清", "不能推出", "容易误读"],
    "### 06｜沉淀一下": ["一个判断", "可复用的视角", "继续追的问题"],
}


def prepare_deep_note_markdown(markdown: str) -> str:
    """Return normalized strict Markdown or raise ValueError with validation errors."""

    normalized = normalize_deep_note_markdown(markdown)
    errors = validate_deep_note_markdown(normalized)
    if errors:
        raise ValueError("invalid deep note Markdown: " + "; ".join(errors))
    return normalized


def normalize_deep_note_markdown(markdown: str) -> str:
    """Apply deterministic formatting cleanup."""

    lines = _trim_before_h1(markdown).splitlines()
    normalized: list[str] = []
    author_seen = False
    decorative_seen_after_author = False

    for line in lines:
        stripped = line.strip()
        if _is_author_variant(stripped):
            normalized.append("> 整理者：Rex Ren")
            author_seen = True
            decorative_seen_after_author = False
            continue
        if author_seen and not decorative_seen_after_author and stripped == DECORATIVE_SEPARATOR:
            normalized.append(DECORATIVE_SEPARATOR)
            decorative_seen_after_author = True
            continue
        if _is_delimiter_variant(stripped):
            normalized.append("---")
            continue
        normalized.append(line.rstrip())

    normalized = _insert_missing_decorative_separator(normalized)
    return "\n".join(normalized).rstrip() + "\n"


def validate_deep_note_markdown(markdown: str) -> list[str]:
    """Return validation errors for strict Rex-native deep-note Markdown."""

    errors: list[str] = []
    lines = markdown.splitlines()
    first = next((line.strip() for line in lines if line.strip()), "")
    if not first.startswith("# "):
        errors.append("first non-empty line must be an H1 title")
    elif not _has_cjk(first[2:]):
        errors.append("H1 title must be a Chinese judgment sentence")

    intro = _intro_chunk(markdown)
    if "> 整理者：Rex Ren" not in intro:
        errors.append("missing author line: > 整理者：Rex Ren")
    if DECORATIVE_SEPARATOR not in intro:
        errors.append(f"missing decorative separator: {DECORATIVE_SEPARATOR}")
    errors.extend(_validate_metadata(intro))
    if not any(line.strip() == "---" for line in lines):
        errors.append("missing section delimiter: ---")
    errors.extend(_validate_required_sections(markdown))
    errors.extend(_validate_personal_view(markdown))
    errors.extend(_validate_references(markdown))
    if _has_inline_numeric_citation(_body_before_references(markdown)):
        errors.append("inline numeric citation markers are not allowed in body")
    if "[generator error:" in markdown.lower():
        errors.append("contains generator error fallback text")
    if "data:image/" in markdown.lower() and "base64" in markdown.lower():
        errors.append("contains base64 image data URI")
    return errors


def _trim_before_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[index:])
    return markdown


def _is_author_variant(stripped: str) -> bool:
    return bool(re.match(r"^>?\s*整理者：", stripped))


def _is_delimiter_variant(stripped: str) -> bool:
    return bool(re.fullmatch(r"[-—─]{3,}", stripped)) and stripped != DECORATIVE_SEPARATOR


def _insert_missing_decorative_separator(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if line.strip() != "> 整理者：Rex Ren":
            continue
        scan = index + 1
        while scan < len(lines) and not lines[scan].strip():
            scan += 1
        if scan < len(lines) and lines[scan].strip() == DECORATIVE_SEPARATOR:
            return lines
        return lines[: index + 1] + ["", DECORATIVE_SEPARATOR] + lines[index + 1 :]
    return lines


def _intro_chunk(markdown: str) -> str:
    return re.split(r"(?m)^---$", markdown, maxsplit=1)[0]


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _validate_metadata(intro: str) -> list[str]:
    errors: list[str] = []
    metadata = _metadata_lines(intro)
    required = ["Source", "Original Title", "Author", "ItemID"]
    for key in required:
        value = metadata.get(key, "").strip()
        if not value:
            errors.append(f"missing metadata field: {key}")
    source = metadata.get("Source", "").strip().lower()
    if source.startswith(("http://", "https://")):
        errors.append("Source must be human-readable, not a URL")
    if "URL" in metadata:
        errors.append("URL metadata is not allowed; put URL in 参考文献")
    return errors


def _metadata_lines(intro: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in intro.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z ]*):\s*(.+?)\s*$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2)
    return metadata


def _validate_required_sections(markdown: str) -> list[str]:
    errors: list[str] = []
    sections = _section_map(markdown)
    for heading in REQUIRED_SECTIONS:
        if heading not in sections:
            errors.append(f"missing section: {heading}")
            continue
        for bullet in REQUIRED_BULLETS.get(heading, []):
            if not _has_bullet(sections[heading], bullet):
                errors.append(f"missing bullet {bullet} in {heading}")
    return errors


def _section_map(markdown: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^### .+$", markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group(0).strip()] = markdown[match.start():end]
    return sections


def _has_bullet(section: str, label: str) -> bool:
    pattern = rf"(?m)^-\s+{re.escape(label)}[：:].+"
    return bool(re.search(pattern, section))


def _validate_personal_view(markdown: str) -> list[str]:
    matches = list(re.finditer(r"(?m)^-\s+我的视角[：:].+", markdown))
    if len(matches) != 1:
        return ["expected exactly one 我的视角 bullet"]
    section_heading = _section_heading_for_position(markdown, matches[0].start())
    if section_heading not in {"### 02｜创新点", "### 03｜与 AI X Simulation 的关系"}:
        return ["我的视角 is only allowed in 02 or 03"]
    return []


def _section_heading_for_position(markdown: str, position: int) -> str:
    headings = list(re.finditer(r"(?m)^### .+$", markdown[:position]))
    if not headings:
        return ""
    return headings[-1].group(0).strip()


def _validate_references(markdown: str) -> list[str]:
    references = _section_map(markdown).get("### 参考文献", "")
    errors: list[str] = []
    if not references:
        errors.append("missing section: ### 参考文献")
        return errors
    if not re.search(r"(?m)^-\s+.+", references):
        errors.append("missing reference bullet in ### 参考文献")
    if re.search(r"(?m)^\[\d+\]", references):
        errors.append("numbered reference labels are not allowed; use bullet references")
    return errors


def _body_before_references(markdown: str) -> str:
    marker = "\n### 参考文献"
    index = markdown.find(marker)
    return markdown if index < 0 else markdown[:index]


def _has_inline_numeric_citation(markdown: str) -> bool:
    return bool(re.search(r"\[\d+\]", markdown))
