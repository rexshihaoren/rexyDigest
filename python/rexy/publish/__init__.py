"""Phase 3 publisher: Selection JSONL -> bilingual public Markdown.

Per ADR-0007 the generator (Phase 2) already populated `translations` on
every SelectionEntry. The publisher is a deterministic, LLM-free renderer
— no Gemini, no fallback chain, no JSON parsing of model output.
"""
