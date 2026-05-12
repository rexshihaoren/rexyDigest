"""Adapter registry / config loading."""

from pathlib import Path

import pytest

from rexy.sources._registry import load_adapters


def test_load_skips_disabled(tmp_path: Path):
    (tmp_path / "arxiv.toml").write_text(
        'source_type = "arxiv"\n'
        'disabled = true\n'
        'categories = ["cs.AI"]\n',
        encoding="utf-8",
    )
    (tmp_path / "rss.toml").write_text(
        'source_type = "rss"\n'
        '[[feeds]]\n'
        'url = "https://example.com/feed"\n'
        'type = "blog"\n',
        encoding="utf-8",
    )
    loaded = load_adapters(tmp_path)
    assert [c.name for c in loaded] == ["rss"]


def test_load_requires_source_type(tmp_path: Path):
    (tmp_path / "broken.toml").write_text(
        'categories = ["cs.AI"]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="source_type"):
        load_adapters(tmp_path)


def test_load_returns_empty_when_dir_missing(tmp_path: Path):
    assert load_adapters(tmp_path / "missing") == []


def test_load_assigns_name_from_filename(tmp_path: Path):
    (tmp_path / "my-arxiv.toml").write_text(
        'source_type = "arxiv"\n'
        'categories = ["cs.AI"]\n',
        encoding="utf-8",
    )
    loaded = load_adapters(tmp_path)
    assert loaded[0].name == "my-arxiv"
    assert loaded[0].source_type == "arxiv"


def test_unknown_source_type_rejected(tmp_path: Path):
    (tmp_path / "weird.toml").write_text(
        'source_type = "spotify"\n',
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="spotify|valid enum value"):
        load_adapters(tmp_path)
