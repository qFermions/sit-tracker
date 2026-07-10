# PROJECT_STATE — Sit Tracker

*A future session should be able to resume from this file alone.*
*Last verified: 2026-07-09, family-beta run (every claim below was exercised on that date).*

## Current practice position

- **Gate 0 — Foundation.** 30 minutes daily at the nostril rim / upper lip; count cycles
  1–8, restart; return without commentary; when the breath goes faint, wait.
- 30-day unbroken streak before booking the first retreat. Progress shows n/30 plus the
  descriptive "days sat, last 30".
- The owner's first real sit is imminent/logged — **treat any browser localStorage as
  production data.** Verification always happens on a throwaway localhost origin.

## App version & schema

- App **v4.0.0** (`CORE.APP_VERSION`), SW cache **v4.0.0** (`sw.js` SW_VERSION — ⚠ bump on
  every HTML edit or installed clients keep the stale shell; the update notice was verified live).
- **Data schema v4** in envelope `jhanaTracker.v2` — see DATA_CONTRACT.md (authoritative).
  v4 adds: session `stability`/`breathClarity` (quick log, null = not reported), envelope
  `feedback[]`, settings `onboarding{done,step}`. Migration chain v1→v2→v3→v4 tested.
- `nimitta` and `aiConfidence` stored names remain permanent.

## Product shape (after the family-beta transformation)

- **Five tabs:** Today · Journal · Progress · Learn · Settings.
- **Today** = status strip (sat-today ✓, streak, works-offline, install hint) + cinematic
  timer (breathing orb + progress arc, calm state colors) + practice preset cards
  (First Sit 30′ recommended · Short Reset 10′ · Steady Breath 20′ · Standard 45′ ·
  Custom · Review previous) + collapsible options + one-line practice guidance.
- **First-launch onboarding**: 3 screens (build practice / start simply / record honestly),
  skippable, resumes its step, never shows over active-sit recovery or once done or when
  real sessions exist (CORE.onboardingState, tested).
- **Journal** = post-sit quick log (contact-minutes slider + confidence + one-tap
  impressions: attention, breath clarity, restlessness, drowsiness + note, ~30 s) with the
  full detail sections (timeline, hindrances, qualities, light/image report, teacher
  review) intact underneath · "Write what you noticed" (local parser → confirmed draft) ·
  searchable history · printable teacher report.
- **Learn** = epistemic legend (practice guidance / traditional claim / personal record),
  the six-level practice map, advanced traditional material, source-library pointer.
- **Settings** adds: install-on-phone guide (environment-aware + offline checklist),
  local-only feedback (copy/download/mailto, stored in envelope), demo data load/remove,
  version line.
- **Private family beta** chip in the header opens the feedback form.
- **Demo/test isolation (hard rule, tested):** synthetic entries (`_test`/`_demo`,
  notes `[TEST DATA]`) are excluded from statistics, streaks, backup reminders, JSON/CSV
  exports, and the teacher report; visible in history with a badge; one-tap removal;
  demo banner shows whenever any exist.

## Verification record (2026-07-09 family-beta run)

- `node tests/run-core-tests.mjs sit-tracker-v2.html` → **271/271** (227 previous + 44 new:
  v3→v4 migration ×8, presets ×5, onboarding ×8, demo isolation ×12, feedback ×7,
  clock-back guard ×4).
- In-app `?selftest=1` → **271/271**, and the clean load produced exactly one console
  message (the self-test log) — zero errors.
- Live Chrome (127.0.0.1:8379): onboarding full walkthrough incl. step-resume after reload
  and "Start my first 30-minute sit" actually starting a 30:00 sit; quick log chips saved
  to schema fields (stability 3, breathClarity 5, restlessness mild); Today strip updates;
  demo loaded → 10 badged entries, real metrics stayed 1 session/1-day streak, teacher
  report and JSON export contained only the real entry → one-tap removal; feedback form →
  formatted report stored locally with copy/download/mailto; AI draft flow + reject safe
  after the DOM restructure; zen mode hides all chrome; mid-sit refresh → resume banner
  (onboarding suppressed) → continue; **SW update path observed live**: bump to v4.0.0 →
  update notice → Reload to update → old cache deleted, data intact; responsive at 360 px
  and 390 px via exact-width iframes (no horizontal overflow; timer scales via
  min(300px,72vw)).
- Fixes this run: TIMER.start re-entry guard (rapid double-click), clock-moved-backwards
  clamp (no bogus "settling in"), invalid `<input>`-inside-`<button>` in the custom preset
  card, synthetic data leaking into stats/streaks/exports (now isolated).

## Architecture

Unchanged layering (ARCHITECTURE.md): pure CORE (now also: presets, onboarding state,
feedback formatting, demo generator, backup logic) · STORE · AUDIO · TIMER · AI · plus UI
modules TODAY / ONBOARD / FEEDBACK / REVIEW / HISTORY / PROGRESS / MAP / JOURNAL /
SETTINGS / APP. `window.__sitTracker` exposes {CORE, STORE, TIMER, AI, REVIEW, APP,
ONBOARD, TODAY} for scripted checks.

## Remaining limitations (honest)

1. No web bell while the screen is locked (platform limit, stated in the UI; ADR-0002).
2. Real iOS/Android devices still untested — mobile checks were desktop-Chrome iframes at
   exact widths; A2HS, standalone storage isolation, and real install prompts unobserved.
3. Screen-reader testing not performed (semantics/labels/live regions are in place;
   no NVDA/VoiceOver pass).
4. No live AI-provider round trip (no key in this environment).
5. Multiple tabs running the same sit: last-writer-wins on the timer key (single-user
   assumption; documented, not guarded).
6. Window-resize automation failed late in the run (OS kept the window maximized), hence
   the iframe method for responsive verification.
7. Print preview of the teacher report was content-verified, not pixel-verified on paper.

## Family distribution (no deploy)

Serve the folder on the home network (`python -m http.server 8080`), open
`http://<computer-ip>:8080/sit-tracker-v2.html` on each phone, follow Settings →
"Install on your phone", run the offline checklist, then testers use "Load demo data"
or their own sits and send feedback via the beta chip.

## Immediate next practice action

Sit 30 minutes today; press Start on the recommended card; log it honestly. Day 1 of 30.
