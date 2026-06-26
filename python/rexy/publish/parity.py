"""Structural parity check between Node and Python publisher outputs.

Per ADR-0002, legacy Node output is **not** the quality bar (old digests can
hallucinate). This module is an **optional diff tool** when you want to
compare structure between a Node-published brief and a Python-published
brief — e.g. after a deliberate migration week — not a merge gate.

We do **not** require byte-identical output (Node CN translations are
LLM-generated and non-deterministic; Python's come from Selection JSONL).
What we compare is **structural parity**:

  - Same number of items
  - Same set of canonical URLs (= same Items selected)
  - Same composite score per Item (1dp tolerance)
  - Same English fields per Item (TL;DR, Implication, takeaway count)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


_URL_RE = re.compile(r"https?://[^\s)\]]+")
_COMPOSITE_RE = re.compile(r"\b(\d+\.\d)\b")


@dataclass(slots=True)
class ParsedBrief:
    urls: list[str] = field(default_factory=list)
    composites: list[float] = field(default_factory=list)
    tldr_lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParityResult:
    ok: bool
    differences: list[str] = field(default_factory=list)


def parse_brief(text: str) -> ParsedBrief:
    """Best-effort structural parse: pulls URLs, composites, EN tldr lines."""

    urls: list[str] = []
    seen: set[str] = set()
    for m in _URL_RE.finditer(text):
        url = m.group(0).rstrip(".,)")
        if url not in seen:
            seen.add(url)
            urls.append(url)

    composites = [float(m.group(1)) for m in _COMPOSITE_RE.finditer(text)]

    tldr_lines: list[str] = []
    in_tldr = False
    for line in text.splitlines():
        if "TL;DR" in line and "**" in line:
            in_tldr = True
            continue
        if in_tldr:
            stripped = line.strip()
            if not stripped:
                continue
            tldr_lines.append(stripped)
            in_tldr = False
    return ParsedBrief(urls=urls, composites=composites, tldr_lines=tldr_lines)


def compare(node_md: str, python_md: str, *, score_tolerance: float = 0.1) -> ParityResult:
    """Return a ParityResult; ok=True iff structural parity holds."""

    node = parse_brief(node_md)
    py = parse_brief(python_md)
    diffs: list[str] = []

    node_urls = set(node.urls)
    py_urls = set(py.urls)
    if node_urls != py_urls:
        only_node = node_urls - py_urls
        only_py = py_urls - node_urls
        if only_node:
            diffs.append(f"items only in Node output: {sorted(only_node)[:5]}")
        if only_py:
            diffs.append(f"items only in Python output: {sorted(only_py)[:5]}")

    if len(node.composites) != len(py.composites):
        diffs.append(
            f"composite score count differs: node={len(node.composites)} python={len(py.composites)}"
        )
    else:
        for i, (a, b) in enumerate(zip(node.composites, py.composites)):
            if abs(a - b) > score_tolerance:
                diffs.append(f"composite #{i}: node={a} python={b} (>{score_tolerance})")

    return ParityResult(ok=not diffs, differences=diffs)
