"""Per-Item payload files under `corpus/payloads/`.

Filenames are derived from `Item.id`: every character outside
``[A-Za-z0-9._-]`` is replaced with ``_`` so the filename is safe on every
filesystem (macOS, Linux, Windows). Long URL-shaped IDs are truncated and
suffixed with a short hash to keep names under 200 chars.

  arxiv:2401.12345        ->  arxiv_2401.12345.txt
  url-sha1:abcd...        ->  url-sha1_abcd....txt
  rss:https://x.y/post/#a ->  rss_https___x.y_post__a__<hash>.txt
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")
_MAX_NAME_LEN = 180  # leaves room for suffix + slack on most filesystems


class PayloadsStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, item_id: str, payload: str | bytes, suffix: str = ".txt") -> str:
        """Write a payload and return the filename (relative to `root`)."""

        if not suffix.startswith("."):
            suffix = "." + suffix
        filename = _safe_filename(item_id, suffix)
        target = self.root / filename
        self.root.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, bytes):
            target.write_bytes(payload)
        else:
            target.write_text(payload, encoding="utf-8")
        return filename

    def read(self, payload_ref: str) -> str:
        return (self.root / payload_ref).read_text(encoding="utf-8")

    def exists(self, payload_ref: str) -> bool:
        return (self.root / payload_ref).exists()


def _safe_filename(item_id: str, suffix: str) -> str:
    safe = _UNSAFE.sub("_", item_id)
    # Cap the name length, but keep enough id-prefix to remain debuggable.
    if len(safe) + len(suffix) > _MAX_NAME_LEN:
        digest = hashlib.sha1(item_id.encode("utf-8")).hexdigest()[:8]
        keep = _MAX_NAME_LEN - len(suffix) - 1 - len(digest)
        safe = f"{safe[:keep]}_{digest}"
    return f"{safe}{suffix}"
