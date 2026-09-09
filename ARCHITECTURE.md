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

## Visual identity system (defined once in `:root`; Apple design pass, 2026-08-26)

Everything visual derives from one token layer at the top of the `<style>` block; no
surface invents its own values. Tokens are named for **purpose**, not appearance. The
full contract, with every contrast ratio computed rather than estimated, is in
`APPLE_DESIGN_SYSTEM.md`.

- **Appearances** — tokens are defined on `:root` for **dark** (the app's home look) and
  redefined for **light** (`prefers-color-scheme: light`), **increased contrast**
  (`prefers-contrast: more`, both appearances) and **reduced transparency**
  (`prefers-reduced-transparency: reduce`, which makes the two glass surfaces opaque).
  No token is defined only inside a media query. `<meta name="color-scheme">` declares
  `dark light`. There is deliberately no in-app theme switch: the app follows the device.
- **Type** — system stack only (zero embedded font bytes). **Four weights only**
  (400/500/600/700) — the previous 650/750 steps rounded to 700/900 on the static
  fallback families, so "one notch above bold" rendered heavier than `h1`. `--fs-timer`
  (clamp 2.2–6rem, weight **400** — Regular, not Light; the floor is in `rem` so it
  scales with the reader's text size and does not overflow a 320 px screen at 200%),
  `--fs-hero` (2.4–3.6rem), `--fs-display` (1.8–2.6rem, weight 700), then xl/lg/md/sm/xs.
  Numerals are always `tabular-nums`. Uppercase is reserved for the two genuinely
  singular labels (`.label-caps`, `.p-tag`); the stat and tile captions render in the
  sentence case they are written in.
- **Colour** — backgrounds `--background` / `--surface` / `--surface-elevated`; labels
  `--label-primary` / `--label-secondary` / `--label-tertiary`; structure `--separator` /
  `--separator-strong`; meaning `--accent`, `--on-accent`, `--accent-muted`,
  `--tradition`, `--success`, `--warning`, `--destructive`, `--danger-edge`.
  Every label token clears **4.5:1 on the worst surface it can legally appear on**, in
  both appearances — measured, and machine-gated by `tests/run-browser-gates.mjs`, whose
  contrast check samples gradient colour stops at worst case so no rendered text is
  skipped. (The previous ramp claimed "all AA on their surfaces" and was not: the
  tertiary step scored 4.16:1 on `--bg3`.)
- **Depth** — three elevation shadows (`--elev-1/2/3`, re-tuned for light) plus one glass
  recipe (`--glass` + blur 16–20px) used only for the dialog and the toast, and dropped
  entirely under reduced transparency.
- **Gradients** — six named recipes, each with a job: `--grad-wash` (page ground),
  `--grad-card` (surface sheen), `--grad-cta` (primary action), `--grad-hero`
  (first-open), `--grad-orb`, `--grad-recommend`. Nothing else gets a gradient.
  *(The previous note claimed "exactly three"; there were already six, three of them
  written as untokenised literals.)*
- **Motion** — `--dur-1/2/3` = 120/220/480ms with one decel curve (`--ease-out`);
  `transform`, `opacity` and `scale` only; press = scale(.97); nothing animates in a loop
  while idle. **The orb breathes only during the settling countdown and is explicitly
  still during the sit itself** — the practice object is the breath, not the screen. That
  rule is gated three ways: a source-string check in `tests/run-core-tests.mjs` and two
  live computed-style checks in the browser gates. The global
  `prefers-reduced-motion` rule kills every animation and transition.
- **Navigation** — a convertible tab bar: bottom-anchored and full width on compact
  widths (thumb-reachable, `env(safe-area-inset-bottom)` aware), top-anchored as a
  centred pill from 768px. Five destinations, no hamburger, no horizontal scrolling at
  any width from 320 to 1024.
- **Targets** — every interactive element renders at least 44×44, verified by measuring
  rendered boxes across all five screens rather than reading declared CSS.

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
