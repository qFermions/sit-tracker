# PROJECT_STATE — Sit Tracker

*A future session should be able to resume from this file alone.*
*Last verified: 2026-07-09 (all checks below were actually run on that date).*

## Current practice position

- **Gate 0 — Foundation.** 30 minutes daily at the nostril rim / upper lip.
- Count each in-and-out cycle 1–8, restart; return without commentary; when the breath
  goes faint, wait rather than breathing harder.
- A 30-day unbroken streak comes before booking the first retreat. The Progress tab
  tracks this explicitly ("Gate 0 target … current: n/30").
- Practice map: Foundation → Consistency → Attention stability → Collectedness &
  reported phenomena → Jhāna investigation → Advanced traditional framework (educational only).

## Tracker version & schema

- App: `sit-tracker-v2.html`, single file, vanilla HTML/CSS/JS, no build system. ~3000 lines.
- **Data schema version: 3** (envelope `jhanaTracker.v2`).
  - v1 = legacy loose keys `janSits`/`janGates` → migrated non-destructively, originals never touched.
  - v2 = envelope without `entrySource`/`teacherReview`/`afterStateReport`.
  - v3 = current. Migration chain v1→v2→v3 implemented in `CORE.migrate` and covered by tests.
- Session fields (nulls mean "not reported", never zero): id, v, date, startTime, endTime,
  plannedMin, actualMin, concMin, ratio (derived), confidence, settleMin, longestSteadyMin,
  wanderings, returns, object(+objectCustom), posture, phase, energyBefore/After,
  calmBefore/After, afterStateReport, hindrances{5 keys→mild|moderate|strong},
  dominantHindrance, qualities[], **nimitta{category,…}** (keep this stored name),
  timeline[], timelineDerivedMin, manualOverride, markers[], notes, journalText,
  entrySource(timer|manual|ai|imported|null), teacherReview(none|flagged|discussed|reviewed),
  teacherNotes, createdAt, updatedAt. AI drafts carry an **aiConfidence** evidence map.
- **Renaming stored fields requires a schemaVersion bump + tested migration. Do not rename for cosmetics.**

## Architecture (preserve this separation)

- `/*CORE-START*/ … /*CORE-END*/` — pure logic, no DOM/localStorage/fetch side-effects:
  parser, timer math (timestamp-based), streaks, metrics, insights, CSV, import, migration,
  validation, provider request/response shaping, and `runSelfTests()`.
- `STORE` — localStorage adapter (memory fallback + banner if unavailable), envelope
  load/save, session CRUD, settings, practice map, separate timer-state key.
- `AUDIO` — WebAudio bells, no assets.
- `TIMER` — wall-clock timestamps only (never tick counting); persists on transitions and
  every 15 s; refresh shows a resume banner; a sleeping tab reconciles correctly; interval
  bells are capped to 1 catch-up bell after sleep; wake-lock with graceful fallback.
- `AI` — provider adapter; local deterministic parser is the default engine and the
  automatic fallback; provider output is schema-validated and rejected if it invents values.
- `REVIEW / HISTORY / PROGRESS / MAP / JOURNAL / SETTINGS / UI` — presentation.
- `window.__sitTracker` exposes {CORE, STORE, TIMER, AI, REVIEW} for automated verification.

## Completed features (all verified 2026-07-09)

- Timer: presets 20–120 + custom, prep countdown, interval/final bells, pause/resume,
  finish-early, reset-with-confirm, quiet-screen mode, Space shortcut, markers (6 kinds),
  refresh recovery, tab-sleep reconciliation (verified live by shifting startMs −5 min).
- Review: ≤30 s basic review (contact-minutes slider + ± + confidence + auto ratio,
  conc ≤ actual enforced), optional detail sections (attention, timeline with derived
  estimate + manual-override display, hindrances, qualities, nimitta report with neutral
  wording, body/energy, notes, teacher review), manual entry, edit, delete-with-confirm.
- Journal AI: local parser handles the canonical spec example exactly (30/7/16-low/9/4/
  restlessness-dominant/none/calmer, hedge-word confidence downgrade, per-field evidence);
  draft → field-by-field editable review → explicit confirm modal (duplicate warning with
  visible comparison) → save; reject button; provider failure falls back visibly (verified
  against an unreachable endpoint); nothing saves silently (verified).
- Progress: 10 metric cards, 16-week consistency calendar, 9 chart blocks with honest
  empty states, deterministic insights with range/n/metric/strength, Gate-0 streak line.
- History: search + 5 filters, full-record detail modal, edit/delete.
- Practice Map: 6 sober levels, evidence states (never auto-set), teacher notes/dates,
  advanced section labels powers 1–5 as traditional claims with no verified demonstration.
- Data: JSON export/import with preview (new/dup/invalid + reasons), CSV export,
  intra-file dedup, malformed-file rejection, corrupt-envelope quarantine, typed-DELETE wipe
  (legacy keys untouched), storage info line.

## Verification record (2026-07-09)

- `node tests/run-core-tests.mjs sit-tracker-v2.html` → **207/207 passed**.
- In-app `?selftest=1` → 207/207, console shows only the self-test log.
- Full inline script passes `node --check` (syntax).
- Live browser run (Chrome, http://127.0.0.1:8377): clean console on load; full workflow
  exercised end-to-end — sit → pause/resume → markers → mid-sit reload + resume banner →
  finish early → review → save (ratio 54%, markers prefilled wanderings/returns) →
  progress update → history search → import preview (1 new/1 dup/1 invalid) → malformed
  import rejected → AI draft → confirm-gated save (verified not saved before confirm) →
  provider-failure fallback → reload persistence. Mobile 375×812: no horizontal overflow.
- Test data created during verification was wiped afterwards; the 127.0.0.1:8377 origin is clean.

## AI provider status

**Not configured** (deliberate). Local parser is the active engine. A live round-trip to a
real provider has **not** been verified in this environment — the adapter was verified
against the Anthropic/OpenAI response shapes in unit tests plus a live failure-path test.
When a key is added via Settings, run *Test connection* once.

## Backup / export procedure

Settings → Export JSON (full backup) → keep a copy off-device. Restore: Settings →
Import JSON → review the preview → confirm. CSV export for teachers/spreadsheets.

## Remaining limitations (real ones)

1. localStorage only (~5 MB, OS-wipeable). Fine for years of sessions (~1 KB each);
   the mitigation is the export habit, not IndexedDB. Documented, honest, adapter-isolated.
2. No live external-provider round-trip verified (no key available in this environment).
3. Bells require one user interaction before audio can play (browser autoplay policy);
   wake-lock is unsupported in some browsers — the sit still times correctly, the screen may sleep.
4. Session timeline is entered post-hoc in Review; markers are captured live but timeline
   segments are not auto-built from markers (possible future enhancement).
5. UI-layer behavior is covered by manual/scripted browser verification, not automated unit
   tests (CORE logic is fully unit-tested; adding a DOM test framework was out of scope by design).
6. History list renders the first 200 matches only (noted in the UI when it truncates).

## Immediate next practice action

Sit 30 minutes today at the nostril rim, counting 1–8. Open the app, press *Start sit*,
and complete the 30-second review honestly. Day 1 of 30.
