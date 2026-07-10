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

No build step exists. "Deploying" means copying the file.

> Note: browser storage is **per origin**. Data saved when opened via `file://` is separate
> from data saved via `http://localhost:8080`. Pick one way of opening the app and stick to it.

## Everyday workflow

1. **Sit** — pick a preset (default 30 min), press *Start sit* (or Space). Optional: prep
   countdown, interval bells, final bell, quiet-screen mode, one-tap markers during the sit.
2. **Review** (~30 seconds) — the review opens automatically when the sit ends. Set the one
   number that matters: *estimated minutes of genuine breath contact* (self-reported, with a
   confidence level). Everything else is optional detail.
3. **Journal AI** — or just write/dictate what happened in plain language. A deterministic
   local parser turns it into a structured **draft** that you confirm field by field.
   Nothing is ever saved without your explicit confirmation.
4. **Progress** — streaks, hours, ratios, settling time, charts, and grounded observations
   computed from your data (never by an AI model).

## Storage & backup

- Data lives in this browser's `localStorage` under the key **`jhanaTracker.v2`**
  (a versioned envelope: `{schemaVersion, sessions, settings, map}`). The in-progress timer
  is persisted separately under `jhanaTracker.v2.timer` so a refresh or crash never loses a sit.
- Legacy v1 keys (`janSits`, `janGates`) are migrated into the envelope automatically and
  are **never modified or deleted**.
- Data is **not encrypted**. It is as private as your browser profile.
- localStorage can be wiped by the OS/browser. **Back up regularly:**
  Settings → *Export JSON (full backup)*. Restore via Settings → *Import JSON…* — you get a
  preview (new / duplicate / invalid counts) before anything is written. CSV export exists
  for spreadsheets and teachers.
- If the stored envelope is ever unreadable, the raw bytes are preserved under a
  `jhanaTracker.v2.recovered-<timestamp>` key rather than discarded.

## AI journaling setup (optional)

The default engine is a **local, deterministic parser** — no network, no key, nothing sent
anywhere. Optionally, Settings → *AI provider* accepts an endpoint URL, model, and API key
(Anthropic Messages API and OpenAI-style chat endpoints are both understood). The key is
stored only in your browser's localStorage, in plain text — never in this repository.

Provider rules, enforced in code: output is validated against a strict schema; malformed or
invented values are rejected; any failure falls back to the local parser with a visible
notice; a draft never saves without your confirmation; the app is fully usable with no
provider configured.

> Calling `api.anthropic.com` directly from a `file://` page requires the
> `anthropic-dangerous-direct-browser-access` header (already sent). Some providers still
> block browser calls via CORS — if so, the local parser simply takes over.

## Testing

Two equivalent ways to run the 207-assertion logic suite:

- **In app:** Settings → *Run self-tests*, or open with `?selftest=1`.
- **Node:** `node tests/run-core-tests.mjs sit-tracker-v2.html`
  (extracts the `/*CORE-START*/ … /*CORE-END*/` block and runs it; exit code 1 on failure).

## Honesty rules (enforced by design and by tests)

- Concentration values are the user's own estimates, labeled *self-reported* everywhere.
- Light/image events are recorded neutrally ("Reported light event"), never as
  "confirmed nimitta", "access concentration", or any attainment claim.
- Pattern observations state their date range, sample size, metric, and evidence strength,
  and never use causal language.
- The Practice Map certifies nothing; "teacher reviewed" can only be set by you.
- Missing information stays null ("not reported") — never silently zero.

## Files

| File | Purpose |
|---|---|
| `sit-tracker-v2.html` | The entire application |
| `tests/run-core-tests.mjs` | Node harness for the CORE logic suite |
| `PROJECT_STATE.md` | Current state — read this first in a new session |
| `IMPLEMENTATION_PLAN.md` | Architecture notes and roadmap |
| `abhinna-practice-manual.md`, `abhinna-6-roadmap.md` | Traditional practice reference (source material, not app docs) |

## Known limitations

See `PROJECT_STATE.md` → *Remaining limitations*.
