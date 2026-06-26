"""Phase 2 generator: corpus -> Selection -> Markdown gist.

Implements the five-stage hybrid ranker from ADR-0004:

  1. prefilter  : in-Window + has-payload + coarse keyword gate
  2. prerank    : Recency * KOL-prior * keyword-density   -> top ~30 shortlist
  3. summarise  : per-Item LLM call -> tldr/takeaways/scores/translations
  4. novelty    : Python: Corpus distance + recency
  5. finalise   : composite, sort, take top N, write Selection JSONL

The renderer that turns the Selection into a Markdown gist lives next door
in `renderer.py` (no LLM, deterministic).
"""
