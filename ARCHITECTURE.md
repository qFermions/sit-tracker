# ARCHITECTURE — Sit Tracker

One file (`sit-tracker-v2.html`) with strict internal layering. Companion platform files
(`manifest.json`, `sw.js`, `icons/`) are optional enhancements — the HTML file alone is the app.

## Layer map (as it exists in the file, top to bottom)

| Layer | Location in file | Contents | Rules |
|---|---|---|---|
| Presentation shell | `<style>` + `<body>` markup | CSS system, static markup for Sit/Journal/Settings, containers for dynamic tabs, print-report container | No logic |
| **Domain (CORE)** | `/*CORE-START*/ … /*CORE-END*/` | Session schema + validation, timer math (wall-clock), timeline derivation, streak/metric/insight computation, CSV, import parsing + dedup, schema migration, journal parser, provider request/response shaping, backup-reminder decision, synthetic-data generator, `runSelfTests()` (227 assertions) | Pure. No DOM, no localStorage, no fetch. Node-extractable. **This is the future iOS contract** — any native client ports or embeds this layer unchanged. |
| Persistence | `STORE` | localStorage adapter (memory fallback), envelope load/save, session CRUD, settings, practice map, timer-state key, test-data purge, corruption quarantine | Only module that touches storage keys |
| Platform adapters | `AUDIO` (WebAudio bells) · `AI` (fetch to optional provider, local-parser fallback) · `APP` (SW registration, persistent-storage request, backup reminder) · `sw.js` (offline cache) | Feature-detected; every one degrades gracefully (file://, no audio, no provider, no SW) |
| Application/presentation | `TIMER`, `REVIEW`, `HISTORY`, `PROGRESS`, `MAP`, `JOURNAL`, `SETTINGS`, `UI` | Orchestration + rendering per tab; templates render from state | Business rules belong in CORE, not here |
| Boot | final IIFE | wiring, tab routing, `?selftest=1`, `window.__sitTracker` test hook | |

## Data flow
User action → module handler → CORE function (validate/compute) → STORE mutation →
re-render affected tabs. The timer never counts ticks: elapsed time is always recomputed
from persisted wall-clock timestamps (`CORE.timerSnapshot`), which is what makes refresh,
tab-sleep, and screen-lock recovery correct by construction.

## Storage keys
- `jhanaTracker.v2` — versioned envelope `{schemaVersion:3, sessions, settings, map, savedAt}`
- `jhanaTracker.v2.timer` — in-progress sit (so ticking never rewrites session data)
- `jhanaTracker.v2.recovered-<ts>` — quarantined unparseable bytes (never discarded)
- `janSits`, `janGates` — legacy v1, read-once migrated, never written or deleted

## Product principles (enforced, not aspirational)
1. **Evidence integrity** — the app records self-reports; it never certifies jhāna, nimitta,
   attainment, or powers. Forbidden wording is guarded by unit tests.
2. **Privacy / local-first** — no accounts, no analytics, no network calls except the
   explicitly configured AI provider; keys live only in localStorage.
3. **Calm UX** — no gamification, no loss-framed streaks, no notifications; reminders are
   dismissible and never appear during a sit; no motion during meditation.
4. **Deterministic over AI** — statistics and insights are computed by CORE code; AI (if
   configured) only drafts, behind schema validation and explicit user confirmation.
5. **Honest platform limits** — mobile bell/lock constraints are stated in the UI rather
   than papered over.
