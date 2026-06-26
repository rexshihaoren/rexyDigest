"""Core domain types for the Rexy Digest pipeline.

Vocabulary defined in CONTEXT.md at the repo root. Read that first if you are
new to the codebase.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any


SCHEMA_VERSION = 1


class PayloadKind(StrEnum):
    """What the adapter actually managed to obtain for an Item.

    Honesty matters here: the renderer downstream branches on this so it
    never invents takeaways from a Payload it does not have.
    """

    METADATA_ONLY = "metadata_only"
    EXTRACT = "extract"
    FULL_TEXT = "full_text"
    UNAVAILABLE = "unavailable"


class SourceType(StrEnum):
    """Enum of supported Source families.

    Used to namespace Item.id (e.g. "arxiv:2401.12345") and pick the right
    Source Adapter at fetch time.
    """

    ARXIV = "arxiv"
    RSS = "rss"
    PODCAST = "podcast"
    YOUTUBE = "youtube"
    BLOG = "blog"


_WINDOW_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})/(\d{4}-\d{2}-\d{2})$")


@dataclass(frozen=True, slots=True)
class Window:
    """An inclusive date range a Selection covers.

    Encoded as `YYYY-MM-DD/YYYY-MM-DD` (start/end) when serialised.
    """

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(f"Window start {self.start} after end {self.end}")

    def contains(self, when: date | datetime) -> bool:
        d = when.date() if isinstance(when, datetime) else when
        return self.start <= d <= self.end

    def __str__(self) -> str:
        return f"{self.start.isoformat()}/{self.end.isoformat()}"

    @classmethod
    def parse(cls, s: str) -> Window:
        m = _WINDOW_RE.match(s.strip())
        if not m:
            raise ValueError(
                f"Invalid Window {s!r}; expected YYYY-MM-DD/YYYY-MM-DD"
            )
        return cls(
            start=date.fromisoformat(m.group(1)),
            end=date.fromisoformat(m.group(2)),
        )


def make_item_id(source_type: SourceType, source_native_id: str | None, url: str | None = None) -> str:
    """Build a namespaced Item.id.

    Falls back to `url-sha1:<hash>` when the source has no native ID. The
    fallback is intentionally typed so a grep of the corpus reveals which
    sources lack stable IDs.
    """

    if source_native_id:
        return f"{source_type.value}:{source_native_id}"
    if url:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        return f"url-sha1:{digest}"
    raise ValueError("Need either source_native_id or url to build an Item id")


@dataclass(slots=True)
class Item:
    """A real piece of published content. Immutable across runs once written.

    Per ADR-0001, Items are intrinsic — per-Brief outputs (scores, tldr,
    takeaways, translations) live on Selection, not here.
    """

    id: str
    source_type: SourceType
    source_native_id: str | None
    canonical_url: str
    title: str
    author: str
    published_at: date
    type: str
    topics_raw: list[str]
    payload_kind: PayloadKind
    payload_ref: str | None
    fetched_at: datetime
    adapter: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        # Construction-time invariants: required fields. Adapters build Items
        # with `payload_ref=None`; the framework patches it after writing the
        # payload. Therefore the payload_kind <-> payload_ref relationship is
        # checked at persistence time (see `validate_for_persistence`), not
        # here.
        if not self.id:
            raise ValueError("Item.id is required")
        if not self.canonical_url:
            raise ValueError(f"Item {self.id}: canonical_url is required")
        if not self.title:
            raise ValueError(f"Item {self.id}: title is required")
        if not self.adapter:
            raise ValueError(f"Item {self.id}: adapter (provenance) is required")
        if self.fetched_at.tzinfo is None:
            raise ValueError(f"Item {self.id}: fetched_at must be timezone-aware")

    def validate_for_persistence(self) -> None:
        """Invariants the corpus enforces at write time.

        After the framework has written a payload (or decided not to), the
        Item is ready for `items.jsonl`. Required relationship:
        `payload_kind in {extract, full_text}` iff `payload_ref` is set.
        """
        wants_ref = self.payload_kind in (PayloadKind.EXTRACT, PayloadKind.FULL_TEXT)
        if wants_ref != (self.payload_ref is not None):
            raise ValueError(
                f"Item {self.id}: payload_ref must be set iff payload_kind is "
                f"extract|full_text (got kind={self.payload_kind}, "
                f"ref={self.payload_ref!r})"
            )

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type.value,
            "source_native_id": self.source_native_id,
            "canonical_url": self.canonical_url,
            "title": self.title,
            "author": self.author,
            "published_at": self.published_at.isoformat(),
            "type": self.type,
            "topics_raw": list(self.topics_raw),
            "payload_kind": self.payload_kind.value,
            "payload_ref": self.payload_ref,
            "fetched_at": self.fetched_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "adapter": self.adapter,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_jsonable(cls, d: dict[str, Any]) -> Item:
        return cls(
            id=d["id"],
            source_type=SourceType(d["source_type"]),
            source_native_id=d.get("source_native_id"),
            canonical_url=d["canonical_url"],
            title=d["title"],
            author=d["author"],
            published_at=date.fromisoformat(d["published_at"]),
            type=d["type"],
            topics_raw=list(d.get("topics_raw") or []),
            payload_kind=PayloadKind(d["payload_kind"]),
            payload_ref=d.get("payload_ref"),
            fetched_at=_parse_iso_datetime(d["fetched_at"]),
            adapter=d["adapter"],
            schema_version=int(d.get("schema_version", SCHEMA_VERSION)),
        )


@dataclass(slots=True)
class Scores:
    """Per-Item scoring outputs (Selection-time, not Item-time).

    `composite = 0.4*relevance + 0.3*novelty + 0.3*actionability` per the
    formula in `prompt_weekly_gist.md` and ADR-0004.
    """

    relevance: float
    novelty: float
    actionability: float
    composite: float

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "relevance": round(float(self.relevance), 2),
            "novelty": round(float(self.novelty), 2),
            "actionability": round(float(self.actionability), 2),
            "composite": round(float(self.composite), 2),
        }

    @classmethod
    def from_jsonable(cls, d: dict[str, Any]) -> Scores:
        return cls(
            relevance=float(d["relevance"]),
            novelty=float(d["novelty"]),
            actionability=float(d["actionability"]),
            composite=float(d["composite"]),
        )

    @staticmethod
    def composite_of(relevance: float, novelty: float, actionability: float) -> float:
        return round(0.4 * relevance + 0.3 * novelty + 0.3 * actionability, 2)


@dataclass(slots=True)
class Translations:
    """Bilingual ZH fields for a Selection entry (per ADR-0007).

    All fields nullable so a partial translation is representable.
    """

    title_zh: str | None = None
    tldr_zh: str | None = None
    takeaways_zh: list[str] | None = None
    implication_zh: str | None = None
    topics_zh: list[str] | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "title_zh": self.title_zh,
            "tldr_zh": self.tldr_zh,
            "takeaways_zh": list(self.takeaways_zh) if self.takeaways_zh else None,
            "implication_zh": self.implication_zh,
            "topics_zh": list(self.topics_zh) if self.topics_zh else None,
        }

    @classmethod
    def from_jsonable(cls, d: dict[str, Any] | None) -> Translations:
        d = d or {}
        return cls(
            title_zh=d.get("title_zh"),
            tldr_zh=d.get("tldr_zh"),
            takeaways_zh=list(d["takeaways_zh"]) if d.get("takeaways_zh") else None,
            implication_zh=d.get("implication_zh"),
            topics_zh=list(d["topics_zh"]) if d.get("topics_zh") else None,
        )


@dataclass(slots=True)
class SelectionEntry:
    """One Item picked for one Window — the per-Brief output.

    Per ADR-0001/0002, `selections/Selection_<end>.jsonl` is the single source
    of truth that both the Markdown gist renderer and the eventual Phase-3
    publisher consume.
    """

    item_id: str
    window: Window
    rank: int
    scores: Scores
    tldr_en: str
    takeaways_en: list[str]
    implication_en: str
    topics: list[str]              # ranker-classified, e.g. ["Agent"], ["Simulation"]
    translations: Translations
    model: str                     # provenance: which LLM produced this entry
    prompt_version: str            # provenance: which prompt template version
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.item_id:
            raise ValueError("SelectionEntry.item_id is required")
        if self.rank < 1:
            raise ValueError(f"SelectionEntry rank must be >= 1, got {self.rank}")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "window": str(self.window),
            "rank": self.rank,
            "scores": self.scores.to_jsonable(),
            "tldr_en": self.tldr_en,
            "takeaways_en": list(self.takeaways_en),
            "implication_en": self.implication_en,
            "topics": list(self.topics),
            "translations": self.translations.to_jsonable(),
            "model": self.model,
            "prompt_version": self.prompt_version,
            "generated_at": self.generated_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    @classmethod
    def from_jsonable(cls, d: dict[str, Any]) -> SelectionEntry:
        return cls(
            item_id=d["item_id"],
            window=Window.parse(d["window"]),
            rank=int(d["rank"]),
            scores=Scores.from_jsonable(d["scores"]),
            tldr_en=d["tldr_en"],
            takeaways_en=list(d["takeaways_en"]),
            implication_en=d["implication_en"],
            topics=list(d.get("topics") or []),
            translations=Translations.from_jsonable(d.get("translations")),
            model=d["model"],
            prompt_version=d["prompt_version"],
            generated_at=_parse_iso_datetime(d["generated_at"]),
        )


@dataclass(slots=True)
class FetchedItem:
    """What a Source Adapter yields per content piece.

    Adapter is pure: it builds the Item with `payload_ref=None` and hands
    the framework the raw payload bytes (or None when payload_kind is
    metadata_only / unavailable). The framework writes the payload to disk,
    derives the filename, and patches `Item.payload_ref` before persisting.
    """

    item: Item
    payload: str | bytes | None = None
    payload_suffix: str = ".txt"  # filename suffix the framework should use

    def __post_init__(self) -> None:
        kind = self.item.payload_kind
        has_payload = self.payload is not None
        wants_payload = kind in (PayloadKind.EXTRACT, PayloadKind.FULL_TEXT)
        if has_payload and not wants_payload:
            raise ValueError(
                f"FetchedItem {self.item.id}: payload supplied but payload_kind is {kind}"
            )
        if wants_payload and not has_payload:
            raise ValueError(
                f"FetchedItem {self.item.id}: payload_kind is {kind} but no payload supplied"
            )


def _parse_iso_datetime(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
