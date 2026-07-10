# PROJECT_STATE — Sit Tracker

*A future session should be able to resume from this file alone.*
*Last verified: 2026-07-10, depth run (every claim below was exercised on that date).*

## Current practice position

- **Gate 0 — Foundation.** 30 minutes daily at the nostril rim / upper lip; count cycles
  1–8, restart; return without commentary; when the breath goes faint, wait.
- 30-day unbroken streak before booking the first retreat. Progress shows n/30 plus the
  descriptive "days sat, last 30".
- The owner's first real sit is imminent/logged — **treat any browser localStorage as
  production data.** Verification always happens on a throwaway localhost origin.

## App version & schema

- App **v4.1.0** (`CORE.APP_VERSION`), SW cache **v4.1.0** (`sw.js` SW_VERSION — ⚠ bump on
  every HTML edit or installed clients keep the stale shell; the update notice was verified
  live again this run: notice → reload → old cache deleted, data intact).
- **Data schema v5** in envelope `jhanaTracker.v2` — see DATA_CONTRACT.md (authoritative).
  v5 adds session `timelineSource` ('markers'|'manual'|null); the tested v4→v5 migration
  marks every pre-v5 timeline 'manual'. Migration chain v1→v5 tested end to end.
- `nimitta` and `aiConfidence` stored names remain permanent.

## Product shape (v4.0.0 family-beta + 2026-07-10 depth run)

- **Five tabs:** Today · Journal · Progress · Learn · Settings. Onboarding, Today home
  (status strip + cinematic timer + preset cards), quick log, demo isolation, local-only
  feedback, install guide — all as shipped in v4.0.0 (see git history for details).
- **Timeline from markers (new):** the review timeline pre-fills from the one-tap in-sit
  markers via `CORE.timelineFromMarkers` (documented convention: steady→mostly steady,
  wandering→wandering, returned→intermittent, dull/agitated→themselves, notable=event
  only; pre-first-marker span is wandering after a wandering/returned first tap, else
  uncertain). Visible "suggested from your in-sit markers" notice; any hand edit flips
  `timelineSource` to 'manual'; the manual contact estimate always wins; nulls stay null.
- **Deterministic insights (new):** Progress has "Ask about your practice" — four canned
  questions answered instantly by CORE (`answerQuestion`): what precedes low-ratio
  sessions (preceding day-gap comparison, bottom tercile vs rest), most frequent
  hindrance, ratio by time of day, settling trend. Every answer carries range, n, metric,
  strength (weak/moderate/reasonably supported/insufficient); hard minimum samples; no
  causal wording (tested). The passive Observations list reuses the same functions.
- **Journal parser round 2 (new):** word-number compounds (twenty-two / thirty five),
  ranges → midpoint + confidence downgrade ('15 or 20', '8 to 10', digit '25-30'),
  clock start-times (hh:mm am/pm, quarter/half past, quarter to; ambiguous bare hours
  become clarifying questions, never guesses), clause-scoped negation ("no restlessness"
  records nothing; "not strong" can't mark strong), "didn't wander" → 0.
- **Provider mock harness (new):** `CORE.MOCK_PROVIDER_RESPONSES` +
  `AI.runMockContract()` exercise the full adapter contract (valid Anthropic/OpenAI,
  malformed, refusal, overclaim, timeout) with no key and no network; failures fall back
  to the local parser with honest messages (`CORE.providerErrorSummary`).
- **Teacher workflow v2 (new):** flag-any-session with a private note from the session
  detail modal (`CORE.nextReviewStateOnFlag`: none→flagged only; never downgrades;
  code can never set 'reviewed'). Teacher report: options dialog (30/90/custom range,
  notes column toggle), flagged appendix with private notes, ⚑ row marks, neutral
  unusual-experience summary (`CORE.unusualExperienceSummary`).
- **Learn build-out (new):** structured summaries from the two practice documents under
  progressive disclosure — sit script, SN 51.20 energy tuning, if-a-light-appears first;
  the wider classical map with per-stage epistemic badges ('scientific finding' added to
  the legend; the powers marked "no verified case in recorded history"); in-app viewers
  show the unaltered .md sources (also cached by the SW for offline).
- **Bilingual scaffold (new):** `CORE.I18N` — English defaults, empty Burmese slots the
  owner fills by hand (machine translation forbidden); `tr()` falls back to English;
  the Settings language toggle appears only once ≥1 screen is fully translated
  (`fullyTranslatedScreens`), so the app ships English-active with the toggle hidden.
- **Data longevity (new):** exports stamped `-YYYYMMDD-HHMM`; storage health leads with
  the age of the last backup (highlighted >14 days / never); README documents the
  recovery procedure; restore rehearsal is CORE-tested (field-level equality) and was
  performed live in a clean context this run.

## Verification record (2026-07-10 depth run)

- `node tests/run-core-tests.mjs sit-tracker-v2.html` → **375/375** (271 previous + 104
  new: timeline-from-markers ×20, v4→v5 migration ×3, insights/questions ×20, parser
  round 2 ×31, provider fixtures/summaries ×9, teacher rules ×9, i18n ×9, restore
  round-trip ×1, plus supporting assertions).
- In-app `?selftest=1` → **375/375**, exactly one app console message (the self-test
  log) — zero errors on clean load.
- Live Chrome (throwaway localhost origins): marker-suggested timeline pre-fill → save →
  provenance 'markers'; hand edit → 'manual', divergence notice, manual wins; envelope
  v4→v5 migration on existing data; Ask-a-question card with honest insufficient-data
  answers; `AI.runMockContract()` — all four failure modes fell back with honest
  messages; flag dialog persisted state + note; report v2 rendered range header,
  appendix, ⚑, honesty footer, notes-column toggle; Learn viewers loaded unaltered
  documents with Burmese intact; onboarding unchanged after the i18n refactor; injected
  Burmese slot rendered (ယနေ့) while empty slots stayed English; restore rehearsal:
  2 rich sessions → clean context import → field-level equality, re-import 0 fresh /
  2 duplicates; **SW update path observed live**: v4.0.0→v4.1.0 notice → reload → old
  cache deleted, sessions intact.
- Fix this run: duration patterns didn't accept hedge words between "for" and the number
  ("sat for about twenty minutes") — caught by a new test, fixed.

## Architecture

Unchanged layering (ARCHITECTURE.md): pure CORE (now also: timelineFromMarkers, insight
question engine, i18n table, teacher rules, provider mock fixtures) · STORE · AUDIO ·
TIMER · AI · UI modules TODAY / ONBOARD / FEEDBACK / REVIEW / HISTORY / PROGRESS / MAP /
JOURNAL / SETTINGS / APP. `window.__sitTracker` exposes {CORE, STORE, TIMER, AI, REVIEW,
APP, ONBOARD, TODAY} for scripted checks. ADR-0001 stay-vanilla intact: single file +
manifest + sw.js + icons; no dependencies, no build.

## Remaining limitations (honest)

1. No web bell while the screen is locked (platform limit, stated in the UI; ADR-0002).
2. Real iOS/Android devices still untested — desktop Chrome only; A2HS, standalone
   storage isolation, and real install prompts unobserved.
3. Screen-reader testing not performed (semantics/labels/live regions in place).
4. No live AI-provider round trip (no key in this environment; the mock harness covers
   the contract, not a real provider's behavior).
5. Multiple tabs running the same sit: last-writer-wins on the timer key.
6. Burmese slots in `CORE.I18N` are all empty by design — the owner supplies them;
   the language toggle stays hidden until at least one screen is complete.
7. Print output was content-verified in DOM, not pixel-verified on paper this run.

## Family distribution (no deploy)

Serve the folder on the home network (`python -m http.server 8080`), open
`http://<computer-ip>:8080/sit-tracker-v2.html` on each phone, follow Settings →
"Install on your phone", run the offline checklist, then testers use "Load demo data"
or their own sits and send feedback via the beta chip.

## Immediate next practice action

Sit 30 minutes today; press Start on the recommended card; log it honestly. After the
sit, tap the markers you actually used — the review timeline will pre-fill itself.
