# Sit Tracker — ဈာန်

A single-file, local-first meditation practice tracker. It records what actually happened
during sits — durations, an honest self-estimate of breath contact, hindrances, and neutral
reports of unusual experiences — without ever pretending software can verify attainment.

**One file. No build. No dependencies. No account. Your data never leaves your device
unless you export it or explicitly configure an AI provider.**

## Run it

- Double-click `sit-tracker-v2.html` (works from `file://`), **or**
- serve the folder: `python -m http.server 8080` or `npx serve`, then open
  `http://localhost:8080/sit-tracker-v2.html`.

No build step exists. "Deploying" means copying the folder.

> Browser storage is **per origin**: data saved under `file://` is separate from data under
> `http://localhost:8080`, and an installed iOS home-screen app has its own container too.
> Pick one way of opening the app; to move data, use Export JSON → Import JSON.

## Install as an app (optional)

When served over http(s) the page is an installable PWA (`manifest.json` + `sw.js` +
`icons/`), and it works fully offline after the first load:

- **Android Chrome:** menu → *Install app* (or the install prompt).
- **iOS Safari:** Share → *Add to Home Screen*. The installed app starts with **empty
  storage** — export from the Safari tab and import inside the installed app once.
  Reliable keep-screen-awake in the installed app needs iOS 18.4+.
- **Desktop Chrome/Edge:** install icon in the address bar.
- Updates: when a new version is deployed, the app shows a calm "Reload to update" notice —
  it never force-reloads.
- On `file://` none of this applies and nothing breaks — the double-click use case is unchanged.

## Everyday workflow

1. **Sit** — pick a preset (default 30 min), press *Start sit* (or Space). Optional prep
   countdown, interval bells, final bell, quiet-screen mode, one-tap markers.
2. **Review** (~30 seconds) — opens automatically when the sit ends. The one number that
   matters: *estimated minutes of genuine breath contact*, self-reported with confidence.
3. **Journal AI** — or write/dictate plain language; the local deterministic parser builds
   a draft you confirm field by field. Nothing saves without explicit confirmation.
4. **Progress** — streaks shown descriptively (plus "days sat of last 30" — a missed day is
   data, not failure), hours, ratios, charts, and deterministic observations.
5. **Teacher report** — Review → History → *Teacher report*: a printable last-30-days
   summary (print to PDF and email it yourself; there is no sharing infrastructure).

## Honest mobile limits

If the screen locks or the browser goes to background, **bells may not sound** — no web
page can ring a locked phone. The elapsed time itself is always correct: the timer works
from wall-clock timestamps and reconciles the moment you return. "Keep screen awake" (on by
default, supported browsers) avoids the problem; a future native wrapper is the real fix
(see `docs/adr/ADR-0002-ios-direction.md`).

## Storage & backup

- Data lives in this browser's `localStorage` under `jhanaTracker.v2` (versioned envelope,
  schema v3 — see `DATA_CONTRACT.md`). The in-progress timer persists separately, so a
  refresh or crash never loses a sit.
- Legacy v1 keys (`janSits`, `janGates`) migrate automatically and are never deleted.
- Data is **not encrypted**. It is as private as your browser profile.
- Settings shows storage health: persistence status, usage estimate, last export. The app
  requests persistent storage where supported, and shows a calm, dismissible export
  reminder when sessions accumulate without a recent backup.
- **Export JSON** is the durability guarantee (browsers can evict site data). The export
  **excludes your AI API key** on purpose — re-enter it after a restore.
- Import shows a preview (new / duplicate / invalid with reasons) before writing anything;
  merging is union-by-id, so importing the same backup twice cannot create duplicates.
- Two devices, no account: put the export file in your own iCloud/Drive folder and import
  on the other device. The file is transport, not truth — the merge handles overlaps.

## AI journaling (optional)

Default engine is a **local, deterministic parser** — no network. Settings → AI provider
accepts endpoint/model/key (Anthropic Messages API and OpenAI-style endpoints understood).
The key is stored only in this browser's localStorage, in plain text, and is stripped from
exports. Provider output is schema-validated; invented values are rejected; failures fall
back to the local parser with a visible notice; drafts never save without confirmation.

## Testing

- **In app:** Settings → *Run self-tests*, or open with `?selftest=1`.
- **Node:** `node tests/run-core-tests.mjs sit-tracker-v2.html` (exit 1 on failure).
- Performance: Settings → Developer → seed 1,000 clearly-marked synthetic sessions
  (`[TEST DATA]`), purge in one click. Exports made while seeded include them — purge first.
- Icons are reproducible: `node tools/make-icons.mjs` (zero dependencies).

## Honesty rules (enforced by design and by tests)

- Concentration values are the user's own estimates, labeled *self-reported* everywhere.
- Light/image events are recorded neutrally — never "confirmed nimitta" or any attainment claim.
- Observations state date range, sample size, metric, and evidence strength; no causal language.
- The Practice Map certifies nothing; "teacher reviewed" can only be set by you.
- Missing information stays null ("not reported") — never silently zero.

## Repository map

| File | Purpose |
|---|---|
| `sit-tracker-v2.html` | The entire application |
| `manifest.json`, `sw.js`, `icons/` | Optional PWA layer (http(s) only) |
| `tests/run-core-tests.mjs` | Node harness for the CORE suite |
| `tools/make-icons.mjs` | Dependency-free icon generator |
| `ARCHITECTURE.md` | Layer map + product principles |
| `DATA_CONTRACT.md` | Every persisted field — the future iOS contract |
| `ROADMAP.md` | Now / Next / Later / Reject, each with evidence |
| `RESEARCH_NOTES.md` | Dated research findings → decisions |
| `docs/adr/` | ADR-0001 (web stack), ADR-0002 (iOS direction) |
| `PROJECT_STATE.md` | Current state — read this first in a new session |
| `abhinna-*.md` | Traditional practice reference (source material) |
