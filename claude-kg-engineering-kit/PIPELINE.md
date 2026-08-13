# PIPELINE — the four stages, and what runs where

The pipeline itself is an explicit graph of responsibilities. Each node has
one job, defined inputs/outputs, a schema, a failure behavior, and a
verification method. The most important design rule: **Claude only does the
work that needs judgment; plain code does everything that can be done
exactly.**

```
   SOURCE INGESTION      (code: load docs, register sha256)
          │
          ▼
      EXTRACTION         (Claude, fast model — schema-constrained)
          │                verified: every quote must exist in the source
          ▼
      RESOLUTION         (Claude, quality model — judgment call)
          │                verified: only given surface forms, one cluster each
          ▼
       ASSEMBLY          (code: ids, dedupe, provenance, validation)
          │                verified: graph integrity errors are fatal
          ▼
    GRAPH VALIDATION     (code: dangling edges, missing citations, …)
          │
          ▼
     QUERY PLANNER       (Claude, quality model — what matters?)
          │
          ▼
   MULTI-HOP RETRIEVAL   (code: deterministic BFS, sorted output)
          │
    ┌─────┴──────────┬───────────────┐
    ▼                ▼               ▼
 PRICING          PRODUCT        FINANCIAL      (Claude analysts,
 ANALYST          ANALYST        ANALYST         bounded questions)
    └─────┬──────────┴───────────────┘
          ▼
  STRATEGIC SYNTHESIZER  (Claude — citations machine-checked)
          │
          ▼
       EVALUATOR         (code: P/R/F1, citation + multi-hop checks)
        /    \
     PASS    FAIL → bounded repair (max N re-asks) → salvage + report
```

## Stage 1 — Extraction (`src/kgkit/extraction.py`, `prompts/extraction.md`)

- **Input:** one document. **Output:** `ExtractionResult` — entity mentions
  (surface form, type, description, quote) and candidate facts (subject,
  predicate, object entity XOR typed scalar, qualifiers, time, uncertainty,
  quote). Schema: `schemas/extraction.schema.json`.
- Structured outputs via the SDK's `client.messages.parse()` with the
  Pydantic model — no JSON parsing, no regex.
- **Verification:** every quote is re-checked against the document
  (whitespace/case-insensitive). Failures trigger a bounded repair re-ask;
  what still fails is dropped and reported (`salvage_extraction`).
- **Honesty:** absence is not zero; unknown is not false; nothing invented.

## Stage 2 — Resolution (`src/kgkit/resolution.py`, `prompts/resolution.md`)

- **Input:** all mentions grouped by type with their per-document
  descriptions. **Output:** `ResolutionResult` — clusters + ambiguous
  groups. Schema: `schemas/resolution.schema.json`.
- Code aggregates deterministically; Claude only makes the judgment call,
  clustering by *meaning* (descriptions), never by string similarity.
- **Validation (code):** members must be real extracted surface forms, each
  in at most one cluster, types must match. Invented members are dropped,
  not trusted. Unclustered surface forms stay their own entities; ambiguous
  groups are preserved onto the graph.
- The demo proves both safety properties: "NRI" merges into Northwind
  Robotics (description-supported), "Northwind Logistics" does not
  (lookalike), "Project Helios" stays ambiguous.

## Stage 3 — Assembly (`src/kgkit/assembly.py`)

- **100% deterministic.** Stable node ids (`company:northwind-robotics`),
  normalized snake_case predicates, sequential edge ids, citations carried
  from facts, source registry with sha256 per document.
- Duplicate facts collapse by content fingerprint (citations union), so
  re-running assembly can't create duplicate edges.
- **Validation** (`GraphStore.validate`) checks: duplicate ids, dangling
  endpoints, object XOR violations, missing citations, citations to
  unknown documents, quotes that don't verify, relations outside a schema
  (when one is supplied), unparsed scalars. Errors here are fatal by design
  — they indicate pipeline bugs, not model noise.

## Stage 4 — Query (`src/kgkit/query.py`)

Three separated steps:

1. **Planning (Claude):** given the question plus the graph's entity list
   and relation types, pick seed entities, relation filters, and hop count
   (clamped to 1–4). Schema: `schemas/query.schema.json`.
2. **Retrieval (code):** breadth-first traversal from the seeds — same
   graph + same plan = same evidence, sorted by edge id. Retracted edges
   never surface; superseded only on request. Predicate filters apply to
   *expansion too*: a filtered-out edge is not crossed to reach nodes
   behind it (bounded retrieval by design — an empty `predicates` list
   follows everything).
3. **Answering (Claude, machine-checked):** the model sees only the
   retrieved evidence and must cite edge ids for every material claim.
   Citations outside the evidence are stripped; an answer left with no
   valid citations becomes "insufficient evidence". If retrieval finds
   nothing, **the model is never called** — the kit answers "insufficient
   evidence" deterministically rather than letting model memory fill gaps.

## Failure behavior everywhere

Semantic stages run inside `run_with_repair` (`src/kgkit/client.py`): one
attempt, then at most `max_repair_attempts` corrective re-asks (live engine
only — fixtures are deterministic), then salvage-and-report. No unbounded
loops anywhere; `tests/test_client.py` pins this.

## Maintenance (adding documents, corrections, migrations)

- **Adding documents:** extract just the new docs, resolve against the
  existing alias set, and `add_node`/`add_edge` — both are idempotent
  merges (aliases/citations union, content-fingerprint dedupe).
- **Superseded facts:** never delete a contradicted edge — set its
  `status` to `"superseded"` and add the new edge. Default traversal hides
  superseded edges; audits can request them (`include_superseded=True`).
- **Retraction:** `status: "retracted"` removes an edge from every query
  while keeping the record of what was once believed.
- **Conflicting claims:** keep both edges with their citations and let
  qualifiers (`source`, `uncertainty`) mark who says what. The answer
  prompt reports conflicts and cites both sides. Never silently overwrite
  historical evidence because a newer extraction disagrees.
- **Re-resolution / alias updates:** re-run resolution over the combined
  mention set; assembly merges into existing node ids where canonical
  names match, and `kgkit validate` warns when one name maps to multiple
  nodes.
- **Schema migrations:** `schema_version` lives in the graph file; migrate
  by loading, transforming, bumping the version, and re-running
  `kgkit validate --docs` so every citation is re-verified.
- **Integrity checks:** run `kgkit validate graph.json --docs <docs dir>`
  on a schedule; it re-verifies every quote against the sources.
