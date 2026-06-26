"""Corpus stores: persistence for Items, Payloads, Selections, Runs.

Layout (per Stage-1 design + ADR-0001/0005):

  corpus/
    items.jsonl                          # one Item per line, upsert by id
    payloads/<id>.<suffix>               # raw text per Item (when payload_kind=extract|full_text)
    selections/Selection_<end>.jsonl     # Phase 2 output (written by generator, not Phase 1)
    runs/Run_<run_id>.json               # provenance, one file per run
"""
