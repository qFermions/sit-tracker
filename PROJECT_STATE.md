# PROJECT_STATE — Sit Tracker

*A future session should be able to resume from this file alone.*
*Last verified: 2026-07-09 evening run (every claim below was exercised on that date).*

## Current practice position

- **Gate 0 — Foundation.** 30 minutes daily at the nostril rim / upper lip; count cycles
  1–8, restart; return without commentary; when the breath goes faint, wait.
- 30-day unbroken streak before booking the first retreat (Progress shows n/30, plus the
  descriptive "days sat, last 30" metric).
- Map: Foundation → Consistency → Attention stability → Collectedness & reported
  phenomena → Jhāna investigation → Advanced traditional framework (educational only).

## Tracker version & schema

- `sit-tracker-v2.html` (~3,150 lines) + optional PWA companions (`manifest.json`,
  `sw.js` SW_VERSION v3.1.0, `icons/` from `tools/make-icons.mjs`).
- **Data schema v3** in envelope `jhanaTracker.v2`; timer under `jhanaTracker.v2.timer`;
  legacy `janSits`/`janGates` migrate non-destructively, never deleted.
- Full field contract: **DATA_CONTRACT.md** (authoritative for any future client).
  Renames require schemaVersion bump + tested migration. `nimitta` and `aiConfidence`
  names are permanent.

## Architecture

See **ARCHITECTURE.md**. Pure CORE block (`/*CORE-START*/…/*CORE-END*/`) = domain layer and
future iOS contract; STORE/AUDIO/TIMER/AI/APP + tab modules around it. Timer is wall-clock
timestamp math — refresh/sleep/lock recovery is correct by construction.

## What exists (all verified this run)

Everything from the 2026-07-09 build (timer with recovery, ≤30 s review, markers,
hindrances/qualities, neutral nimitta reports, Journal AI local parser + provider adapter
with confirm-gated saves, progress dashboard, deterministic insights, history with filters,
sober practice map, export/import/CSV, self-tests), **plus this run's additions:**

- **3A Data safety:** storage health panel in Settings (persistence status via
  `navigator.storage.persisted()`, usage estimate, last-export date); opportunistic
  `persist()` request; calm dismissible backup reminder (CORE.backupStatus: ≥10 sessions,
  never during a sit, 7-day snooze); **AI key stripped from JSON exports**.
- **3B Mobile:** 44 px touch targets everywhere; safe-area insets; `inputmode` numeric
  keyboards; verified 390×844 and 844×390 with zero horizontal overflow; honest
  lock-screen bell note under sit options; immediate reconcile-tick on visibilitychange.
- **3C PWA:** manifest + versioned cache-first sw.js (registered on http(s) only, file://
  untouched, never intercepts provider calls) + generated icons (192/512/maskable/apple-touch,
  dependency-free generator); visible non-forcing "Reload to update" flow.
- **3D Accessibility:** polite live-region announcements at timer phase changes only;
  labeled dialog; contrast bump (--fg-dim #98a4b3, --fg-faint #7e8b99 on dark bg); existing
  focus/reduced-motion/labels retained.
- **3E Visual:** identity preserved; descriptive consistency metric ("days sat, last 30 —
  a missed day is data, not failure").
- **3F Performance:** 1,000-session seed via Settings → Developer (deterministic PRNG,
  `[TEST DATA]`-marked, one-click purge, `_test` flag): seed <1 s, history render ~107 ms
  (200-item cap), progress ~111 ms. Real sessions untouched by purge (verified).
- **Teacher report** (research-driven): History → printable last-30-days summary,
  excludes test data, honesty footer, print CSS.

## Verification record (2026-07-09 evening)

- `node tests/run-core-tests.mjs sit-tracker-v2.html` → **227/227** (207 previous + 20 new:
  backupStatus ×9, synthetic sessions ×9, daysSatLast30 ×2).
- In-app `?selftest=1` → 227/227 expected (final check in Stage 5 of the run log).
- Live Chrome (127.0.0.1:8378): SW registered; storage health rendered honestly (persist
  not granted on a fresh origin — correct); timer announcement fired; reminder appeared at
  1,001 unexported sessions, snoozed to +7 days, suppressed during sits; teacher report
  built and excluded test data; purge removed exactly the 1,000 synthetic sessions;
  provider-fallback and confirm-gate re-verified in Stage 1; mobile portrait/landscape clean.
- Known verification caveat: SW caching serves stale HTML during development — unregister
  SW + delete caches (or bump SW_VERSION) after editing the file. Real deployments must
  bump `SW_VERSION` in sw.js with every HTML change.

## Decisions on record

- **ADR-0001:** stay vanilla single-file; migration triggers codified. Recommendation only.
- **ADR-0002:** Capacitor is the recommended future iOS path (locked-screen bell is the
  driver); readiness gates G1–G6; nothing scaffolded.
- **ROADMAP.md:** Now (done) / Next / Later / Reject with evidence per entry.
- **RESEARCH_NOTES.md:** 10 dated findings with sources.

## AI provider status

Not configured (deliberate). Local parser is the engine. No live provider round-trip has
ever been verified in this environment; adapter verified by unit tests + live failure-path test.

## Remaining limitations (real)

1. No web bell while the screen is locked — platform limit, stated in the UI; native
   wrapper is the fix (ADR-0002).
2. localStorage (~5 MB): fine to ~4,000 sessions; IndexedDB deferred behind the adapter
   until the quota nears (ROADMAP → Later).
3. No live AI-provider round-trip verified (no key in this environment).
4. Real iOS/Android devices untested — all mobile verification was emulated viewports in
   desktop Chrome; iOS-specific behaviors (A2HS, standalone storage isolation, wake lock)
   are documented from primary sources, not observed.
5. Install prompt/standalone mode not observed (requires real install; SW registration and
   caching were observed).
6. Timeline segments are not auto-suggested from markers yet (ROADMAP → Next).
7. UI layer covered by scripted browser verification, not automated DOM tests.

## Immediate next practice action

Sit 30 minutes today; record it. The streak page tells the truth either way.
