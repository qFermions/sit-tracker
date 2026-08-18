# ADR-0003 — HTML payload ceiling: raise 300 KiB → 336 KiB for the practice-training release

Status: **Accepted for the practice-training run.**
Date: 2026-08-18

## Context
The single-file app carries all logic, UI, copy, and its own test suite inline;
PROJECT_STATE has enforced a 307,200-byte (300 KiB) ceiling on `sit-tracker-v2.html`.
At v4.3.0 the file is 306,367 bytes — 833 bytes of headroom.

The practice-training mission adds: a durable practice-mode concept with a saved
one-tap preset, three new post-sit self-report fields (with schema v6 migration and
validation), a rebuilt Learn tab that distinguishes four teaching lineages instead of
presenting one synthesis, new observational Progress questions, and regression tests
for all of it (tests are inline CORE assertions, so they also count against the
ceiling). Honest sizing of that work is ~20–28 KB even after externalizing all
long-form source material.

## What we did first (simplify before spending)
1. **Externalized long-form content.** The detailed source ledger
   (`PRACTICE_SOURCES.md`) lives beside the app as a markdown companion — the same
   pattern already used for the two abhinna documents — readable in-app via the
   existing `openDoc` viewer and precached by the service worker. Only compact,
   immediately-usable module cards stay inline.
2. **Reused existing systems** (badges, `details` disclosure, quick-log chip rows,
   insight-engine scaffolding, preset cards) rather than adding new CSS or widgets.

Even with both, the feature set cannot fit in 833 bytes.

## Decision
Raise the payload ceiling to **344,064 bytes (336 KiB)** and make it a hard,
machine-checked gate: `tests/run-core-tests.mjs` now fails if the file exceeds the
ceiling, so future growth is caught by the same command that runs the test suite
(previously the ceiling lived only in prose).

## Why this is a recorded tradeoff, not drift
- The growth is user-facing practice value and its regression protection — not
  dependencies, frameworks, fonts, or decoration. ADR-0001 (stay vanilla: no build,
  no deps) is untouched.
- 336 KiB remains a single small file by any modern measure (median mobile page
  weight is measured in megabytes); measured domInteractive was ~102 ms at 296 KiB
  and this class of growth does not change that materially.
- The ceiling stays a ceiling. The run landed at ~341 KB (≈3 KB headroom) —
  the sourced Learn content and its regression tests cost more than first
  budgeted, and content quality was chosen over trimming distinctions. The
  next feature run therefore starts by trimming or by a new ADR with the same
  simplify-first obligation; the gate makes silent drift impossible.

## Trigger conditions for re-evaluation
1. The file approaching 336 KiB again → repeat simplify-first; consider moving the
   self-test corpus to a companion file loaded only under `?selftest=1` (kept inline
   today because file:// double-click must be able to self-verify).
2. Measured load-time regression on real phone hardware.
3. ADR-0001 trigger 5 (≥ ~6,000 lines with navigation cost) firing.
