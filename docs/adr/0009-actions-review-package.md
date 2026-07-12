# GitHub Actions Review Package is the production review input

## Context

GitHub Actions generates the weekly Selection, Gist, and Brief from a temporary
Corpus. Git synchronises the human-readable Markdown through Obsidian, but the
ignored Corpus does not travel with it. Local DeepNote generation could
therefore use stale or independently generated Items and Payloads.

## Decision

Each successful Weekly Gist run builds and commits one immutable, checksummed
**Review Package**, named by Window end date and GitHub run ID. It contains only the Window's
Selection, referenced Items and Payloads, matching Provenance, generator
configuration, Gist, and Brief.

`rexy review latest` runs `git pull --ff-only`, finds the latest package under
`Weekly_Gist/Review_Packages/`, verifies all declared checksums, and copies its
Corpus into a local `.rexy/reviews/<run-id>/` workspace. It never merges package
records into the machine-local `corpus/`.

The Gist and generated Brief are sibling automatic artifacts under
`Weekly_Gist/`. Human-reviewed outputs are written to `KnowledgeCard_Inbox/`,
which remains the downstream KnowledgeCard boundary.

## Consequences

- Review is reproducible from one run and fails closed on missing or modified
  evidence.
- Obsidian Git pull remains useful for readable history but is not a data plane
  for DeepNote evidence.
- Historical `Weekly_Gist/Public/` files remain as archival examples; new runs
  do not add files there.
- Local `corpus/` remains available for development and manual experiments.
