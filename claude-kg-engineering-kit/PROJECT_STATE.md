# PROJECT_STATE.md — recovery map

*A fresh session should be able to resume from this file alone. Evidence
lives in git history, tests, and eval run records — this file is the map.*

## Product identity

**Claude Knowledge Graph Engineering Kit for Multi-Agent Systems** — a
sellable kit (code + prompts + schemas + docs) that turns documents into a
provenance-carrying JSON knowledge graph via Claude, answers multi-hop
questions with edge-level citations, and runs specialist analyst agents +
a synthesizer over the shared graph. Two tracks: A = runnable Python/API
kit; B = Claude Projects prompt pack (no code required).

Lives in `/home/user/claude-kg-engineering-kit` — its own git repo,
**fully isolated from the unrelated Sit Tracker repo** at
`/home/user/sit-tracker` (verified untouched: clean tree at fcd0e55).

## Current objective

Phase 7 (buyer docs) → Phase 8 (packaging) → Phase 9 (independent review)
→ Phase 10 (final state).

## Verified milestones (all reproduced by commands below)

- Source verification done (SOURCES.md): official Anthropic cookbook
  "Knowledge graph construction with Claude" (2026-03-23) + "Building
  Effective AI Agents" verified; the alleged "2026 KG-for-multi-agent
  paper" could NOT be verified as Anthropic — recorded as UNVERIFIED.
- Core engine: Pydantic contract, JSON graph store, quote-verified
  provenance, deterministic BFS traversal, bounded repair loops.
- Semantic stages behind an Engine boundary (live `messages.parse`
  structured outputs / offline fixtures / test mocks).
- Demo runs end-to-end offline: 6 fictional docs → 10 nodes / 19 edges /
  6 sources → grounded Q&A (incl. correct "insufficient evidence" refusal)
  → 3 analysts → synthesis citing 10 edges across 5 documents.
- Resolution safety proven by test: NRI alias merged; Northwind Logistics
  decoy NOT merged; "Project Helios" ambiguity preserved on the graph.
- Eval harness with real metrics: extraction P=1.0/R=0.95 (gold contains a
  fact fixtures deliberately miss), resolution pairs 1.0/1.0, QA accuracy
  1.0, citation validity 1.0, multihop pass 1.0. Run records + compare.
- Schemas exported from models (tools/export_schemas.py), drift-tested.

## Test commands and results (last run this session)

- `python3 -m pytest` → **66 passed** (offline, no API key, ~0.2s)
- `python3 -m kgkit.cli demo --engine fixture` → full demo incl. citation
  trail (works from kit root)
- `python3 -m kgkit.cli eval run --suite all --engine fixture` → metrics
  above, records in evals/runs/ (gitignored output)

## Architecture decisions that still matter

- Single JSON graph file, no database; deterministic code for everything
  checkable (assembly, traversal, validation, citation checking).
- Provenance = verbatim quotes, machine-verified against source docs at
  every stage; invalid citations are stripped, unsupported answers are
  downgraded to "insufficient evidence"; empty evidence short-circuits
  without a model call.
- LLM-facing models avoid open dicts (structured-outputs requires
  additionalProperties:false) — qualifiers/attributes are key/value lists.
- Fixture engine = recorded stage outputs, clearly labeled, never sold as
  live responses. Repair loop retries only on live engines, bounded by
  config.max_repair_attempts.
- Analysts are one implementation + role config (documented simplification
  of the suggested pricing.py/product.py/financial.py).
- Models are env-configurable (KGKIT_FAST_MODEL / KGKIT_QUALITY_MODEL);
  defaults claude-haiku-4-5 / claude-opus-5, verified 2026-08-13.

## Known failures / limitations (current)

- Live API smoke test: **NOT RUN — no authorized API credential available**
  in this environment (checked: ANTHROPIC_API_KEY absent). Offline suite
  covers everything deterministic; live behavior is exercised by the same
  code path (`messages.parse`) but unverified here. Documented in
  LIMITATIONS.md.
- Surface-map collisions across entity types pick the first node
  deterministically (documented limitation).

## Source-verification status

Complete — see SOURCES.md (classes: OFFICIAL / THIRD-PARTY / UNVERIFIED /
ORIGINAL, access-dated 2026-08-13).

## Packaging status

DONE and clean-room verified (2026-08-13):
- `dist/Claude-Knowledge-Graph-Engineering-Kit-v1.zip` built from
  `git archive` (tracked files only) minus PROJECT_STATE.md and
  SALES_COPY.md (internal/owner-only) and evals/runs.
- sha256 recorded in dist/SHA256SUMS.
- Clean-room: extracted ZIP into a fresh temp dir → new venv →
  `pip install -e . pytest` → **66 passed** → `kgkit demo` full output →
  `kgkit eval run --suite all` wrote run records. All from the artifact.
- test_package.py's ZIP checks (no .git/.env/caches/run logs; required
  docs present) are active and passing.

## Independent review (Phase 9) — DONE 2026-08-13

Six fresh-context adversarial reviewers (install/usability, api/schema,
graph/provenance, evaluation validity, attribution/hygiene,
marketing/Track B; ~1.3M tokens, 210 tool calls) attempted to disprove
readiness. Verdict: **1 BLOCKING** (QUICKSTART's documented install didn't
install pytest — the buyer's first verification step failed) and ~20
NON-BLOCKING findings, against ~35 VERIFIED_PASS confirmations (all core
guarantees held under adversarial probing; metrics recomputed by hand
matched; ZIP clean; no secrets in tree or history; attribution honest).

The blocker and 12 highest-value non-blocking findings were fixed
(commit "Fix independent-review findings..."), each with a regression
test — suite grew 66 → **74 passing**. Accepted-as-documented instead of
changed: resolution gold's single effective pair (demo-sized, disclosed),
keyword-check limits (now documented in EVALUATION.md), RAG argument
(re-hedged as architectural, not benchmarked). Owner-decision items are in
SALES_COPY's checklist (naming/trademark option).

The ZIP was rebuilt from the fixed tree and the clean-room buyer path
re-verified end to end (venv → pip install -e ".[dev]" → 74 passed →
demo → evals). New sha256 in dist/SHA256SUMS.

## Exact next action

Phase 10: push for durability. GitHub App cannot create repos (403
verified), so: bundle this repo's history, add the kit as a top-level
directory on sit-tracker's session branch claude/project-scope-billing-kwadv3
via a DETACHED WORKTREE (sit-tracker checkout untouched; zero sit-tracker
files modified on the branch), push, open a DO-NOT-MERGE draft retrieval
PR, subscribe to it. Owner extracts the standalone repo with:
`git clone claude-kg-engineering-kit/claude-kg-engineering-kit.bundle`.
