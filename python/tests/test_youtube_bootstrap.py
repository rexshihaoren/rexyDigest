"""youtube_bootstrap: seed channel IDs + TOML render invariants."""

from __future__ import annotations

from rexy.generate.config import GeneratorConfig
from rexy.sources.youtube_bootstrap import (
    YOUTUBE_SEED,
    missing_seed_slugs,
    render_youtube_toml,
    validate_seed_channel_ids,
)


def test_validate_seed_channel_ids_ok():
    validate_seed_channel_ids()


def test_render_includes_all_seeded_slugs_in_priors_order():
    cfg = GeneratorConfig()
    body = render_youtube_toml(cfg)
    assert "source_type = \"youtube\"" in body
    assert "disabled    = false" in body
    assert body.count("[[channels]]") == len(YOUTUBE_SEED)
    # Order follows kol_priors insertion order (defaults): karpathy before simon, etc.
    assert body.index("kol            = \"karpathy\"") < body.index(
        'kol            = "simon willison"'
    )


def test_missing_seed_lists_expected_gaps():
    cfg = GeneratorConfig()
    miss = missing_seed_slugs(cfg)
    assert "lilian weng" in miss
    assert "karpathy" not in miss
    assert len(miss) == len(cfg.kol_priors) - len(YOUTUBE_SEED)
