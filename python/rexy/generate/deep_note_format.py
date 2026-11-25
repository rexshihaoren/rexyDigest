"""Normalize and validate Rex-native KnowledgeCard deep-note Markdown."""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import date
from math import sqrt

logger = logging.getLogger(__name__)

DECORATIVE_SEPARATOR = "──────────────────────────────"

LEGACY_SECTIONS = [
    "### 00｜为什么在意这篇",
    "### 01｜尝试回答的问题",
    "### 02｜创新点",
    "### 03｜与 AI X Simulation 的关系",
    "### 04｜关键论据",
    "### 05｜习惯性反思",
    "### 06｜沉淀一下",
    "### 参考文献",
]

LEGACY_BULLETS = {
    "### 00｜为什么在意这篇": ["直觉", "它戳中的变化", "持续观察的方向"],
    "### 01｜尝试回答的问题": ["长期问题", "急迫性", "切入点"],
    "### 02｜创新点": ["关键论点", "为什么成立"],
    "### 03｜与 AI X Simulation 的关系": ["连接点", "重要性", "还差一步"],
    "### 04｜关键论据": ["支撑材料", "最可信的点", "可被challenge"],
    "### 05｜习惯性反思": ["还没说清", "不能推出", "容易误读"],
    "### 06｜沉淀一下": ["一个判断", "可复用的视角", "继续追的问题"],
}

BULLET_LABEL_ALIASES = {
    "### 01｜核心主张": {"边界": {"适用范围"}},
    "### 03｜反方": {"最强反解释": {"最佳反解释", "最强替代解释"}},
    "### 02｜创新点": {
        "为什么成立": {
            "为什么这个判断成立",
            "为什么它成立",
            "为什么说得通",
            "成立依据",
            "成立理由",
            "论证依据",
            "判断依据",
            "支撑理由",
            "支撑逻辑",
            "原因",
            "理由",
            "依据",
        },
    },
    "### 03｜与 AI X Simulation 的关系": {
        "重要性": {
            "为什么重要",
            "为什么这重要",
            "为什么它重要",
            "为什么关键",
            "重要在哪里",
            "重要之处",
            "关键性",
            "意义",
            "价值",
            "关键价值",
        },
    },
    "### 04｜关键论据": {
        "支撑材料": {
            "证据",
            "证据材料",
            "主要证据",
            "核心证据",
            "证据与案例",
            "支撑证据",
            "支撑资料",
            "支撑论据",
            "支撑案例",
            "案例",
            "案例材料",
            "事实依据",
            "来源依据",
            "关键依据",
            "依据",
            "论据",
            "论据材料",
            "材料依据",
            "实证材料",
            "观察材料",
            "材料",
        },
    },
}

HOOK = "### 00｜钩子与变化"
CLAIMS = "### 01｜核心主张"
EVIDENCE = "### 02｜证据"
COUNTER = "### 03｜反方"
MAP = "### 04｜与我的地图的关系"
SYNTHESIS = "### 05｜沉淀"
REFERENCES = "### 参考文献"
REQUIRED_SECTIONS = (HOOK, CLAIMS, EVIDENCE, COUNTER, SYNTHESIS, REFERENCES)
_TOP_BULLET = re.compile(r"^-\s+(\S.*)$")
_CLAIM_LABEL = re.compile(r"主张([1-9][0-9]*)")
_ISO_DATE = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")
_OTHER_CALENDAR_DATE = re.compile(
    r"(?<!\d)(?:\d{4}\s*(?:年|[-/.]\s*\d)|"
    r"(?:by|before|until|end of)\s+(?:the\s+end\s+of\s+)?\d{4}\b)",
    re.IGNORECASE,
)


def prepare_deep_note_markdown(markdown: str) -> str:
    """Return normalized strict Markdown or raise ValueError with validation errors."""

    normalized = normalize_deep_note_markdown(markdown)
    errors = validate_deep_note_markdown(normalized, allow_legacy=False)
    sections = _section_map(normalized)
    for label, value in _fields(sections.get(SYNTHESIS, "")):
        if label == "待验证预测":
            errors.extend(_validate_prediction_dates(value, date.today()))
    if errors:
        raise ValueError("invalid deep note Markdown: " + "; ".join(errors))
    claims = [value for label, value in _fields(sections[CLAIMS]) if _is_claim(label)]
    for label, value in _fields(sections[SYNTHESIS]):
        if any(_likely_restatement(claim, value) for claim in claims):
            logger.warning("Deep Note %s may restate a core claim", label)
    return normalized


def normalize_deep_note_markdown(markdown: str) -> str:
    """Apply deterministic formatting cleanup."""

    lines = _trim_before_h1(markdown).splitlines()
    normalized: list[str] = []
    author_seen = False
    decorative_seen_after_author = False
    current_heading = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            current_heading = stripped
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
        normalized.append(_normalize_bullet_label(line.rstrip(), current_heading))

    normalized = _insert_missing_decorative_separator(normalized)
    return "\n".join(normalized).rstrip() + "\n"


def validate_deep_note_markdown(markdown: str, *, allow_legacy: bool = True) -> list[str]:
    """Validate a draft, with optional support for saved seven-section notes."""

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
    sections = _section_map(markdown)
    if allow_legacy and LEGACY_SECTIONS[0] in sections and HOOK not in sections:
        errors.extend(_validate_legacy_sections(sections))
        errors.extend(_validate_personal_view(markdown))
    else:
        errors.extend(_validate_current_sections(markdown, sections))
    errors.extend(_validate_references(sections))
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


def _normalize_bullet_label(line: str, heading: str) -> str:
    aliases = BULLET_LABEL_ALIASES.get(heading)
    if not aliases:
        return line
    match = re.match(r"^(\s*-\s+)([^：:]+)([：:])(.*)$", line)
    if not match:
        return line
    prefix, label, delimiter, rest = match.groups()
    label_clean = label.strip()
    for canonical, variants in aliases.items():
        if label_clean in variants:
            return f"{prefix}{canonical}{delimiter}{rest}"
    return line


def _intro_chunk(markdown: str) -> str:
    return re.split(r"(?m)^---$", markdown, maxsplit=1)[0]


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _validate_metadata(intro: str) -> list[str]:
    errors: list[str] = []
    metadata = _metadata_lines(intro)
    required = ["Source", "Original Title", "Author"]
    for key in required:
        value = metadata.get(key, "").strip()
        if not value:
            errors.append(f"missing metadata field: {key}")
    source = metadata.get("Source", "").strip().lower()
    if source.startswith(("http://", "https://")):
        errors.append("Source must be human-readable, not a URL")
    if "URL" in metadata:
        errors.append("URL metadata is not allowed; put URL in 参考文献")
    if "ItemID" in metadata:
        errors.append("ItemID metadata is not allowed; keep item ids in filename and deep_picks TOML")
    return errors


def _metadata_lines(intro: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in intro.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z ]*):\s*(.+?)\s*$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2)
    return metadata


def _validate_legacy_sections(sections: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for heading in LEGACY_SECTIONS:
        if heading not in sections:
            errors.append(f"missing section: {heading}")
            continue
        for bullet in LEGACY_BULLETS.get(heading, []):
            if not _has_bullet(sections[heading], bullet):
                errors.append(f"missing bullet {bullet} in {heading}")
    return errors


def _validate_current_sections(markdown: str, sections: dict[str, str]) -> list[str]:
    headings = re.findall(r"(?m)^### .+$", markdown)
    expected = list(REQUIRED_SECTIONS)
    if MAP in sections:
        expected.insert(4, MAP)
    errors = [f"missing section: {heading}" for heading in expected if heading not in sections]
    if errors:
        return errors
    if [heading.rstrip() for heading in headings] != expected:
        errors.append("sections must use the canonical order without duplicates or extra headings")

    if not 1 <= len(_bullets(sections[HOOK])) <= 2:
        errors.append(f"{HOOK} requires one or two bullets")

    fields = _fields(sections[CLAIMS])
    claim_fields = [(label, value) for label, value in fields if _is_claim(label)]
    claims = [label for label, _ in claim_fields]
    numbered = [f"主张{index}" for index in range(1, len(claims) + 1)]
    if (
        (claims != ["主张"] and (len(claims) < 2 or claims != numbered))
        or any(not value.strip() for _, value in claim_fields)
        or len(_bullets(sections[CLAIMS])) != len(claims) + 1
    ):
        errors.append("use one 主张 or consecutive numbered claims starting with 主张1")

    for heading, labels in (
        (CLAIMS, ("边界",)),
        (COUNTER, ("最强反解释",)),
        (SYNTHESIS, ("可复用的视角", "待验证预测")),
    ):
        for label in labels:
            values = [value for field, value in _fields(sections[heading]) if field == label]
            has_content = len(values) == 1 and (
                bool(values[0].strip())
                or (label == "边界" and _has_bullet(sections[heading], label))
            )
            if not has_content:
                errors.append(f"expected one non-empty {label} bullet in {heading}")
            elif label == "可复用的视角" and not _is_heuristic(values[0]):
                errors.append("可复用的视角 must be a question or an if-then heuristic")

    errors.extend(_validate_evidence(sections[EVIDENCE], claims))
    if MAP in sections and len(_bullets(sections[MAP])) < 2:
        errors.append(f"{MAP} requires two bullets when present; otherwise omit it or use a tag in {HOOK}")
    return errors


def _bullets(section: str) -> list[str]:
    return [match[1] for line in section.splitlines() if (match := _TOP_BULLET.match(line))]


def _fields(section: str) -> list[tuple[str, str]]:
    return re.findall(r"(?m)^- +([^：:\n]+)[：:]([^\n]*)$", section)


def _is_claim(label: str) -> bool:
    return label == "主张" or bool(_CLAIM_LABEL.fullmatch(label))


def _validate_evidence(section: str, claims: list[str]) -> list[str]:
    entries = _bullets(section)
    if not entries:
        return ["missing evidence bullet in 02"]
    errors = []
    matched = set()
    for index, entry in enumerate(entries, 1):
        match = re.match(r"^(主张[1-9][0-9]*)[：:]\s*(.*)", entry)
        if match and match[1] in claims:
            matched.add(match[1])
        elif match or len(claims) > 1:
            errors.append(f"evidence bullet {index} must reference a declared numbered claim")
        content = match[2] if match else entry
        if content.startswith("[未验证]"):
            if not content.removeprefix("[未验证]").strip():
                errors.append(f"evidence bullet {index} must explain the missing evidence")
            continue
        tags = re.findall(r"\[([^\[\]]+)\]", content)
        for choices in ({"一手", "二手"}, {"单源", "多源"}):
            if sum(tag in choices for tag in tags) != 1:
                errors.append(f"evidence bullet {index} needs one of {'/'.join(sorted(choices))}")
        if not re.sub(r"\[[^\[\]]+\]", "", content).strip():
            errors.append(f"evidence bullet {index} must describe the evidence")
    if len(claims) > 1:
        errors.extend(f"missing evidence or [未验证] for {claim}" for claim in claims if claim not in matched)
    return errors


def _is_heuristic(value: str) -> bool:
    return value.rstrip().endswith(("？", "?")) or bool(
        re.search(r"(?:如果|若|当).+(?:就|则|那么).+|\bif\b.+\bthen\b.+", value, re.I)
    )


def _validate_prediction_dates(value: str, today: date) -> list[str]:
    errors = []
    for match in _ISO_DATE.finditer(value):
        deadline = match[0]
        try:
            parsed = date.fromisoformat(deadline)
        except ValueError:
            errors.append(f"待验证预测 has an invalid calendar date: {deadline}")
        else:
            if parsed <= today:
                errors.append(f"待验证预测 deadline must be after {today.isoformat()}: {deadline}")
    if _OTHER_CALENDAR_DATE.search(_ISO_DATE.sub("", value)):
        errors.append("待验证预测 calendar deadlines must use YYYY-MM-DD")
    return errors


def _likely_restatement(claim: str, takeaway: str) -> bool:
    def bigrams(value: str) -> Counter[str]:
        chars = "".join(char for char in value.casefold() if char.isalnum())
        return Counter(a + b for a, b in zip(chars, chars[1:]))

    left, right = bigrams(claim), bigrams(takeaway)
    if min(sum(left.values()), sum(right.values())) < 8:
        return False
    dot = sum(count * right[gram] for gram, count in left.items())
    norm = sqrt(sum(n * n for n in left.values()) * sum(n * n for n in right.values()))
    return dot / norm >= 0.8


def _section_map(markdown: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^### .+$", markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group(0).strip()] = markdown[match.start():end]
    return sections


def _has_bullet(section: str, label: str) -> bool:
    pattern = re.compile(rf"^-\s+{re.escape(label)}[：:](.*)$")
    lines = section.splitlines()
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        if match.group(1).strip():
            return True
        for next_line in lines[index + 1:]:
            stripped = next_line.strip()
            if not stripped:
                continue
            if next_line.startswith((" ", "\t")):
                return True
            return False
    return False


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


def _validate_references(sections: dict[str, str]) -> list[str]:
    references = sections.get(REFERENCES, "")
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
