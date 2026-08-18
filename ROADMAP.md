# ROADMAP — Sit Tracker

Every entry cites its evidence (RESEARCH_NOTES.md §n, PROJECT_STATE.md, or a dated run).
Protected differentiators (never trade away): no account, no paywall, offline, exportable
data, evidence-honest labels (RESEARCH_NOTES §5).

## Now (done in the 2026-08-18 practice-training run, v4.4.0)
- Practice-mode system (`nostril_breath`, schema v6) + persistent one-tap sit
  configuration; timer completions auto-save with the review as enrichment;
  three nullable one-tap reflection rows (clearest spot / subtle breath /
  pleasant feeling). Evidence: docs/design/practice-training-design.md.
- Learn rebuilt around a four-tradition source map (MN 118 as-written, Pa-Auk,
  Brasington, Thai Forest), a jhāna module with the no-certification boundary,
  and divergence-preserving troubleshooting; every card sourced + labeled;
  ledger in PRACTICE_SOURCES.md (SW-precached, readable in-app).
- Orb static during the running sit (settle animation only in prep) — the
  screen no longer competes with the breath.
- Progress: three new deterministic questions under the same honesty contract.
- ADR-0003 payload ceiling (336 KiB) + SW/app version match, both enforced by
  the test runner. Suite 394 → 447.

### Earlier (2026-07-11 visual-identity run)
- Identity system: token layer (brave system-stack type, midnight palette AA-audited,
  glass, three gradients, motion vocabulary), documented in ARCHITECTURE.md.
- First-open hero; Today signature screen (stat tiles, hero timer, oversized CTA);
  Progress/History/Learn/dialog restyles; icon + manifest refresh. Sit screen exempt.
- Share card (canvas, story+square, sober wording, demo-proof, CORE-tested), invite
  text (product voice, no links, tested), demo entry polish.
- Fixes: dialog centering (margin reset vs UA auto), tab-bar overflow at 360/390.

### Earlier (2026-07-10 depth run)
- Timeline suggested from in-sit markers (CORE.timelineFromMarkers, provenance-tracked,
  manual always wins) — was "Next: auto-suggest timeline segments".
- Deterministic insight engine: four canned questions in Progress answered locally with
  range/n/metric/strength and hard minimum samples.
- Journal parser round 2 (compounds, ranges, clock times, negations) + mock
  provider-contract harness (valid/malformed/refusal/overclaim/timeout, no key).
- Teacher workflow v2: flag-with-note, report range picker (30/90/custom), flagged
  appendix, unusual-experience summary — was "Next: teacher report options".
- Learn build-out from the two practice documents, epistemic badges incl. 'scientific
  finding', in-app source viewers (offline-cached).
- Bilingual scaffold: CORE.I18N with empty owner-filled Burmese slots; toggle hidden
  until a screen is fully translated; no machine translation ever.
- Data longevity: date+time export names, prominent last-backup age, tested + live
  restore rehearsal, README recovery procedure. Schema v5 (timelineSource).

### Earlier (2026-07-09 family-beta run)
- First-launch onboarding (3 screens, skippable, step-resume, CORE-tested).
- Today home: status strip, preset cards (30' recommended), cinematic timer (orb + arc).
- Post-sit quick log (one-tap impressions -> schema v4 stability/breathClarity + hindrances).
- IA: five tabs (Today / Journal / Progress / Learn / Settings); deep material under Learn with epistemic legend.
- Demo mode with hard isolation (stats/streaks/exports/report) + one-tap removal.
- Local-only feedback path (copy/download/mailto) + Private-family-beta chip.
- In-app install guide with offline checklist; live-verified SW update notice.
- Fixes: timer re-entry guard, clock-back clamp, synthetic-data leakage.

### Earlier in the same day (platform run)
- Storage health panel + `persist()` request + calm export reminder — §2.
- Installable PWA (manifest, SW, icons) with file:// unchanged — §1.
- Mobile hardening: 44px targets, safe areas, numeric keyboards, landscape, honest
  lock-screen bell note, wake-on-visible reconciliation — §3, §4.
- Accessibility: live-region phase announcements, dialog labeling, AA contrast bump.
- Printable teacher report (last 30 days, excludes test data) — §10.
- Descriptive consistency metric ("days sat, last 30") — §6.
- 1,000-session performance validation + gated seeding tool.
- API key stripped from JSON exports (privacy defect found while writing DATA_CONTRACT).

## Next (evidence exists, not yet built)
- Physical-device pass (iPhone Safari + Android Chrome): install, offline checklist, wake lock, print. Discovered: window-resize automation unreliable — test on real hardware.
- Screen-reader pass (VoiceOver/NVDA) over onboarding, quick log, timer announcements.
- Multi-tab timer guard (storage-event watch or Web Locks; currently last-writer-wins).
- Custom date range on Progress (CORE.filterRange already supports {from,to}; the teacher
  report already has one).
- Owner fills the Burmese slots in CORE.I18N screen by screen (the toggle appears by itself).
- Import preview: show which device/export a file came from (add exportedBy stamp) — §9.
- iOS PWA data-move guide with screenshots (export in Safari → import in installed app) — §1.

## Later (needs a trigger, not effort)
- Capacitor iOS wrapper for locked-screen bells — gates G1–G6 in ADR-0002 — §8.
- IndexedDB behind the existing adapter — trigger: envelope approaching ~5 MB
  (≈4,000+ sessions); today 1,001 sessions ≈ 700 KB — §2.
- Voice dictation into Journal (Web Speech API, feature-detected).
- Optional local-only reminder via Notifications API — must stay non-guilt-framed (§6);
  needs a design that cannot become streak pressure.

## Reject (with reasons)
- **Framework migration** — working, tested, single-maintainer app; no trigger condition met (ADR-0001, §7).
- **Accounts / cloud sync service** — file-based export + user's own cloud folder covers the
  two-device case without custody of user data (§9).
- **CRDT sync library** — union-merge-by-ID already gives the needed semantics for an
  append-mostly log; a library adds cascading complexity for zero current benefit (§9).
- **Streak freezes / guilt notifications / gamification** — documented as manipulative and
  practice-distorting; the app shows descriptive history instead (§6).
- **Teacher sharing platform** — real teacher workflows use conversation + ordinary
  documents; the printable report is the whole feature (§10).
- **Encryption-at-rest claims** — browser storage cannot be meaningfully encrypted against
  a local attacker without a password UX that risks data loss; we say "not encrypted"
  honestly instead (decision rule 4).
- **AI-computed statistics or AI "teacher" persona** — deterministic CORE only; evidence
  rule is non-negotiable.
