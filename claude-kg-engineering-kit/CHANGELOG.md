# CHANGELOG

## v1.0.0 — 2026-08-13

First release.

- Four-stage pipeline (extraction → resolution → assembly → query) with
  Claude structured outputs (`messages.parse` + Pydantic) behind a
  swappable engine boundary (live / fixture / mock).
- Quote-based provenance verified by machine at every stage; citations
  machine-checked in answers, analyst reports, and synthesis.
- Persistent JSON knowledge graph with integrity validation, deterministic
  multi-hop traversal, supersede/retract lifecycle, idempotent merges.
- Multi-agent layer: pricing/product/financial analysts + synthesizer over
  the shared graph (orchestrator-workers).
- Evaluation harness: entity/relation P/R/F1, pairwise resolution metric
  with false-merge audit, multi-hop QA and citation checks, versioned run
  records, run comparison.
- Competitive-intelligence demo: 6 fictional documents, offline fixtures,
  gold datasets; runs with no API key.
- 66 offline tests; schemas exported from the Pydantic models; Claude
  Projects (Track B) instructions.
