"""ArxivAdapter offline tests — fake `arxiv` in sys.modules (no real package or network)."""

from __future__ import annotations

import sys
import types
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from rexy.domain import PayloadKind, Window
from rexy.sources.arxiv_adapter import ArxivAdapter


def _fake_arxiv_module(fake_client: MagicMock) -> types.ModuleType:
    """Minimal stand-in for `import arxiv` inside ArxivAdapter.fetch."""
    m = types.ModuleType("arxiv")
    m.Client = MagicMock(return_value=fake_client)
    m.Search = MagicMock()
    m.SortCriterion = types.SimpleNamespace(SubmittedDate=object())
    m.SortOrder = types.SimpleNamespace(Descending=object())
    return m


class _FakeAuthor:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeResult:
    def __init__(
        self,
        entry_id: str,
        published: datetime,
        title: str,
        summary: str,
        *,
        authors: list[_FakeAuthor] | None = None,
        categories: list[str] | None = None,
    ) -> None:
        self.entry_id = entry_id
        self.published = published
        self.title = title
        self.summary = summary
        self.authors = authors or [_FakeAuthor("A. Author")]
        self.categories = categories or ["cs.AI"]


def test_arxiv_yields_in_window_filters_keywords_stops_at_old():
    window = Window.parse("2026-05-01/2026-05-10")
    adapter = ArxivAdapter(
        name="arxiv_test",
        config={"categories": ["cs.AI"], "keywords": ["agent"], "max_results": 50},
    )
    in_win = _FakeResult(
        "http://arxiv.org/abs/2605.00001v1",
        datetime(2026, 5, 5, tzinfo=timezone.utc),
        "My agent paper",
        "We study multi-agent coordination.",
    )
    no_kw = _FakeResult(
        "http://arxiv.org/abs/2605.00002v1",
        datetime(2026, 5, 6, tzinfo=timezone.utc),
        "Quantum gravity only",
        "No matching vocabulary in this abstract.",
    )
    too_old = _FakeResult(
        "http://arxiv.org/abs/2601.00001v1",
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        "Old paper about agents",
        "Still has agent keyword.",
    )
    # Descending by date: May 6, May 5, Jan 1 — adapter breaks after crossing below window.start
    fake_client = MagicMock()
    fake_client.results.return_value = iter([no_kw, in_win, too_old])

    with patch.dict(sys.modules, {"arxiv": _fake_arxiv_module(fake_client)}):
        items = list(adapter.fetch(window))

    assert len(items) == 1
    fi = items[0]
    assert fi.item.id == "arxiv:2605.00001"
    assert fi.item.published_at == date(2026, 5, 5)
    assert fi.item.payload_kind is PayloadKind.EXTRACT
    assert "multi-agent" in (fi.payload or "").lower()
    fake_client.results.assert_called_once()


def test_arxiv_skips_future_published_then_yields():
    window = Window.parse("2026-05-01/2026-05-10")
    adapter = ArxivAdapter(
        name="arxiv_test",
        config={"categories": ["cs.AI"], "keywords": [], "max_results": 10},
    )
    future = _FakeResult(
        "http://arxiv.org/abs/2605.09999v1",
        datetime(2026, 12, 1, tzinfo=timezone.utc),
        "Future paper",
        "Abstract.",
    )
    ok = _FakeResult(
        "http://arxiv.org/abs/2605.00003v1",
        datetime(2026, 5, 2, tzinfo=timezone.utc),
        "On time",
        "Body.",
    )
    fake_client = MagicMock()
    fake_client.results.return_value = iter([future, ok])

    with patch.dict(sys.modules, {"arxiv": _fake_arxiv_module(fake_client)}):
        items = list(adapter.fetch(window))

    assert len(items) == 1
    assert items[0].item.id == "arxiv:2605.00003"
