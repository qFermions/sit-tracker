One-file vanilla app; pure CORE block is the only place business logic may live.

- `sit-tracker-v2.html` is the entire app: CSS → HTML → `/*CORE-START*/` pure logic
  `/*CORE-END*/` → STORE/AUDIO/TIMER/AI/REVIEW/HISTORY/PROGRESS/MAP/JOURNAL/SETTINGS/UI → boot.
- CORE has no DOM/localStorage/fetch side-effects and is extracted+run under Node by
  `tests/run-core-tests.mjs`. Keep new logic there, never in UI handlers.
- No build system, no package.json, no framework — deliberate product decisions, not gaps.
- Timer is wall-clock timestamp math (`timerSnapshot(state, nowMs)`); never count ticks.
  Interval bells cap at 1 catch-up ring after a tab sleeps (CORE.dueBells).
- `window.__sitTracker` exposes {CORE, STORE, TIMER, AI, REVIEW} for scripted browser checks.
- CSS gotcha fixed once already: any element with a `display:` class rule needs the global
  `[hidden]{display:none!important}` rule to stay hideable — it exists near the top of the CSS; don't remove it.
