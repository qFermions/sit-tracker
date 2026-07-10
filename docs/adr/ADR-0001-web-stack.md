# ADR-0001 — Web stack: stay vanilla single-file vs migrate to a framework

Status: **Recommended — stay vanilla.** (Recommendation only; migration would require
explicit future approval and is not started anywhere in this repo.)
Date: 2026-07-09

## Context
sit-tracker-v2.html is ~3,100 lines of vanilla HTML/CSS/JS: a pure CORE domain block
(227 unit assertions, node-runnable) plus thin module IIFEs (STORE/AUDIO/TIMER/AI/UI…).
One developer, one user, local-first, no server, works from file://. The question recurs:
would React/Vue/Svelte make this better?

## Evidence (see RESEARCH_NOTES.md §7)
- Framework benefits concentrate where this app has no pain: deeply shared reactive state,
  team conventions, large component reuse. Current DOM code is render-from-state templates
  per tab — no observed state-sync bugs in two verified runs.
- Framework cost is concrete for a solo maintainer: build tooling (violates the
  double-click-and-run product requirement), dependency/version churn as recurring unpaid
  work, and a rewrite that would invalidate a working, tested artifact.
- Browser APIs are the stable platform here; the CORE block is already framework-agnostic
  and would survive any future port unchanged — that is the real investment.

## Decision (recommendation)
Stay vanilla single-file. Invest in module discipline (CORE purity, marker-delimited
sections) instead of a framework. No build system, no npm dependencies, no TypeScript.

## Trigger conditions that would justify re-evaluation
1. Recurring DOM/state synchronization bugs traced to hand-rolled rendering (≥3 distinct
   incidents).
2. The same interactive widget hand-implemented a third time.
3. A second regular contributor joins.
4. A required feature that genuinely fights direct DOM code (virtualized 10k-row lists,
   real-time collaborative editing).
5. The single file exceeding ~6,000 lines with demonstrated navigation/maintenance cost.

If triggered: the migration path is a build-time split (CORE → importable module, UI →
components), keeping localStorage schema and DATA_CONTRACT.md unchanged. Until then,
any rewrite proposal lives in ROADMAP.md → Reject.
