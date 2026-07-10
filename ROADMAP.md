# ROADMAP — Sit Tracker

Every entry cites its evidence (RESEARCH_NOTES.md §n, PROJECT_STATE.md, or a dated run).
Protected differentiators (never trade away): no account, no paywall, offline, exportable
data, evidence-honest labels (RESEARCH_NOTES §5).

## Now (done in the 2026-07-09 run)
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
- Auto-suggest timeline segments from in-sit markers (markers already captured;
  reduces review friction — §5 "low-friction logging"; PROJECT_STATE known limitation).
- Custom date range on Progress (CORE.filterRange already supports {from,to}).
- Teacher report options: pick range (30/90/custom), include/exclude notes column — §10.
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
