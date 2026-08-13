# SOURCES.md — Verified source map and attribution

Every important method in this kit is listed here with where it came from and how
sure we are about that. Verification was performed on **2026-08-13** with live web
lookups against first-party pages. Nothing below was copied into the product;
sources were used to understand engineering methods, and all code, prompts,
schemas, examples, and documentation in this kit are original work.

## Source classes

- **OFFICIAL** — verified first-party Anthropic publication.
- **THIRD-PARTY** — engineering material by others; useful context, not Anthropic.
- **UNVERIFIED** — a reference we could not confirm exists as described.
- **ORIGINAL** — created for this product during this build.

## Verified sources

### 1. Knowledge graph construction with Claude (Claude Cookbook)
- **Class:** OFFICIAL (Anthropic)
- **Publisher:** Anthropic, Claude Cookbook. Published 2026-03-23.
- **URL:** https://platform.claude.com/cookbook/capabilities-knowledge-graph-guide
- **Accessed:** 2026-08-13
- **Informed:** the staged pipeline shape (extraction → resolution → assembly →
  query), per-stage model selection (fast model for high-volume extraction,
  stronger model for resolution/synthesis), description-based entity resolution
  (clustering by meaning rather than string similarity), structured outputs via
  `client.messages.parse()` with Pydantic models, subgraph serialization for
  multi-hop querying, and precision/recall evaluation against gold triples.
- **What this kit adds beyond it:** span-level provenance that survives to the
  final answer, explicit ambiguity preservation in resolution, a deterministic
  assembly/validation layer, a runnable evaluation harness with run records and
  prompt-version comparison, a multi-analyst layer over a shared graph, and an
  offline fixture engine so everything runs without an API key.

### 2. Building Effective AI Agents
- **Class:** OFFICIAL (Anthropic)
- **Publisher:** Anthropic Engineering, December 2024.
- **URL:** https://www.anthropic.com/engineering/building-effective-agents
- **Accessed:** 2026-08-13
- **Informed:** the multi-agent patterns used here — orchestrator-workers
  (analysts as bounded workers converging on a synthesizer) and
  evaluator-optimizer (the eval → inspect → change → re-run improvement loop) —
  plus the "simplest architecture that works" principle this kit follows.

### 3. Effective harnesses for long-running agents
- **Class:** OFFICIAL (Anthropic)
- **Publisher:** Anthropic Engineering, 2025-11-26. (Search results name
  Justin Young as author; we could not load the article page itself from
  the build environment to confirm the byline, so treat the author
  attribution as reported, not verified.)
- **URL:** https://www.anthropic.com/engineering — blog index; locate the
  post by its title there (deep link not captured during verification)
- **Accessed:** 2026-08-13 (existence and date verified via search)
- **Informed:** durable-state practices referenced in MULTI_AGENT_PATTERNS.md:
  checkpointed progress files, test gates between stages, and structured
  handoffs — mirrored here as the persistent graph JSON + eval run records.

### 4. Claude API documentation (Claude Docs)
- **Class:** OFFICIAL (Anthropic)
- **Publisher:** Anthropic, https://platform.claude.com/docs
- **Accessed:** 2026-08-13
- **Informed:** current SDK usage (`anthropic` Python SDK ≥0.100,
  `client.messages.parse()` structured outputs, `output_config.format`),
  current model IDs (`claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5`),
  structured-output schema limitations (no `additionalProperties` other than
  `false`, which is why LLM-facing models here use typed lists instead of
  open dicts), and pricing quoted in SCALING.md (date-stamped there).

## References that could NOT be verified as described

### 5. "A 2026 working note / paper: Knowledge Graph Engineering for Multi-Agentic Systems"
- **Class:** UNVERIFIED as an Anthropic publication.
- **What we found (2026-08-13):** no Anthropic paper or working note with this
  title exists that we could locate. The phrase circulates in third-party
  commentary from mid-2026 (e.g. explainx.ai's "Graph Engineering" post of
  2026-07-18, a working note by Peter Steinberger, and community blog posts)
  discussing Anthropic's cookbook guide (source #1) and multi-agent topology
  design. **This kit does not claim such a paper exists and does not attribute
  it to Anthropic.** The engineering substance those posts point at is covered
  by sources #1–#3.

### 6. "Graph Engineering", "Loop Engineering", "Harness Engineering" (as named disciplines)
- **Class:** THIRD-PARTY community terminology.
- **Notes:** "Harness engineering" traces to Anthropic's harness post (source
  #3) but the *-engineering* naming convention is community usage. "Loop
  engineering" (the agent as a model in a loop) traces to community writing,
  often attributed to Andrej Karpathy's framing; we found no formal publication
  by that title. These words are used in this kit's docs only as informal
  vocabulary, never as citations.

## Original work created during this build

- **Class:** ORIGINAL — all of: the `kgkit` source code, all prompts in
  `prompts/`, all JSON Schemas in `schemas/`, the fictional
  competitive-intelligence document set and every company/person/number in it
  (Northwind Robotics, Aurora Dynamics, Northwind Logistics, etc. are invented
  for this product and any resemblance to real companies is coincidental),
  the gold evaluation datasets, the offline fixtures, and all documentation.

## Redistribution note

No third-party article, paper, or PDF is included in this repository or the
buyer package. The demo corpus is fictional and written for this product, so it
is fully redistributable.
