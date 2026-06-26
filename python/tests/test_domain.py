"""Domain invariants — these are the contract Items must satisfy."""

from datetime import date, datetime, timezone

import pytest

from rexy.domain import (
    FetchedItem,
    Item,
    PayloadKind,
    SourceType,
    Window,
    make_item_id,
    now_utc,
)


def _make_item(**overrides):
    base = dict(
        id="arxiv:2401.12345",
        source_type=SourceType.ARXIV,
        source_native_id="2401.12345",
        canonical_url="https://arxiv.org/abs/2401.12345",
        title="A paper",
        author="Someone",
        published_at=date(2026, 5, 7),
        type="paper",
        topics_raw=["cs.AI"],
        payload_kind=PayloadKind.EXTRACT,
        payload_ref="arxiv_2401.12345.txt",
        fetched_at=datetime(2026, 5, 10, 12, tzinfo=timezone.utc),
        adapter="arxiv",
    )
    base.update(overrides)
    return Item(**base)


class TestWindow:
    def test_parse_roundtrip(self):
        w = Window.parse("2026-05-03/2026-05-10")
        assert str(w) == "2026-05-03/2026-05-10"
        assert w.contains(date(2026, 5, 5))
        assert w.contains(date(2026, 5, 3))  # inclusive start
        assert w.contains(date(2026, 5, 10))  # inclusive end
        assert not w.contains(date(2026, 5, 2))

    def test_inverted_window_rejected(self):
        with pytest.raises(ValueError, match="after end"):
            Window(start=date(2026, 5, 10), end=date(2026, 5, 3))

    def test_bad_string_rejected(self):
        with pytest.raises(ValueError, match="Invalid Window"):
            Window.parse("2026-05-10")


class TestMakeItemId:
    def test_namespaces_with_native_id(self):
        assert make_item_id(SourceType.ARXIV, "2401.12345") == "arxiv:2401.12345"
        assert make_item_id(SourceType.YOUTUBE, "abc123") == "youtube:abc123"

    def test_falls_back_to_url_sha1(self):
        out = make_item_id(SourceType.RSS, None, "https://example.com/foo")
        assert out.startswith("url-sha1:")
        # deterministic
        assert out == make_item_id(SourceType.RSS, None, "https://example.com/foo")

    def test_requires_id_or_url(self):
        with pytest.raises(ValueError):
            make_item_id(SourceType.RSS, None, None)


class TestItemInvariants:
    def test_happy_path_roundtrip(self):
        it = _make_item()
        clone = Item.from_jsonable(it.to_jsonable())
        assert clone.to_jsonable() == it.to_jsonable()

    def test_naive_fetched_at_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            _make_item(fetched_at=datetime(2026, 5, 10, 12))

    def test_required_fields(self):
        with pytest.raises(ValueError, match="title"):
            _make_item(title="")
        with pytest.raises(ValueError, match="canonical_url"):
            _make_item(canonical_url="")
        with pytest.raises(ValueError, match="adapter"):
            _make_item(adapter="")


class TestFetchedItem:
    def test_payload_required_when_kind_says_so(self):
        # Adapter constructs the Item with payload_ref=None; framework sets
        # the ref AFTER writing the payload bytes. The FetchedItem invariant
        # is on the relationship between `payload` (bytes) and `payload_kind`.
        item = _make_item(payload_kind=PayloadKind.EXTRACT, payload_ref=None)
        with pytest.raises(ValueError, match="no payload supplied"):
            FetchedItem(item=item, payload=None)

    def test_payload_forbidden_when_kind_is_metadata_only(self):
        item = _make_item(payload_kind=PayloadKind.METADATA_ONLY, payload_ref=None)
        with pytest.raises(ValueError, match="payload supplied but payload_kind"):
            FetchedItem(item=item, payload="abstract")


class TestValidateForPersistence:
    def test_extract_without_payload_ref_rejected(self):
        item = _make_item(payload_kind=PayloadKind.EXTRACT, payload_ref=None)
        with pytest.raises(ValueError, match="payload_ref must be set"):
            item.validate_for_persistence()

    def test_metadata_only_with_payload_ref_rejected(self):
        item = _make_item(payload_kind=PayloadKind.METADATA_ONLY, payload_ref="x.txt")
        with pytest.raises(ValueError, match="payload_ref must be set"):
            item.validate_for_persistence()

    def test_extract_with_payload_ref_accepted(self):
        item = _make_item(payload_kind=PayloadKind.EXTRACT, payload_ref="x.txt")
        item.validate_for_persistence()  # should not raise

    def test_metadata_only_without_payload_ref_accepted(self):
        item = _make_item(payload_kind=PayloadKind.METADATA_ONLY, payload_ref=None)
        item.validate_for_persistence()  # should not raise
