"""KOL detection: shared signal used by prefilter and prerank.

KOL identity can land on an Item in two ways:

1. **Author substring** — historical default. Configured `kol_priors` keys
   are case-insensitive substrings checked against `item.author`.
2. **Topic marker** — adapters that know their channel/feed maps to a
   curated KOL inject ``kol:<slug>`` into ``item.topics_raw``. The slug is
   matched case-insensitively against `kol_priors` keys too.

Items with **any** KOL signal bypass the keyword-density gate in prefilter
(per merge gate: ingest/rank favors KOL-relevant sources) and get the
**maximum** matching prior multiplied into their pre-rank score.
"""

from __future__ import annotations

from ..domain import Item
from .config import GeneratorConfig


_KOL_TOPIC_PREFIX = "kol:"
_DEFAULT_PRIOR = 1.0


def is_kol_item(item: Item, config: GeneratorConfig) -> bool:
    """True if the Item carries any recognised KOL signal."""

    return kol_prior(item, config) > _DEFAULT_PRIOR


def kol_prior(item: Item, config: GeneratorConfig) -> float:
    """Strongest matching KOL prior, or 1.0 if none match.

    Both author substrings and ``kol:<slug>`` topic markers feed the same
    `kol_priors` dictionary, so configuring one KOL once is enough.
    """

    if not config.kol_priors:
        return _DEFAULT_PRIOR

    prior = _DEFAULT_PRIOR
    priors_lc = {k.lower(): float(v) for k, v in config.kol_priors.items()}

    author_lc = (item.author or "").lower()
    for kol, weight in priors_lc.items():
        if kol and kol in author_lc:
            if weight > prior:
                prior = weight

    for topic in item.topics_raw or ():
        if not isinstance(topic, str):
            continue
        if not topic.lower().startswith(_KOL_TOPIC_PREFIX):
            continue
        slug = topic[len(_KOL_TOPIC_PREFIX):].strip().lower()
        if not slug:
            continue
        weight = priors_lc.get(slug)
        if weight is None:
            for kol, w in priors_lc.items():
                if kol and (kol in slug or slug in kol):
                    weight = w
                    break
        if weight is not None and weight > prior:
            prior = weight

    return prior
