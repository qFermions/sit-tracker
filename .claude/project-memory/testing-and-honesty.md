Confirmed test commands, AI-adapter rules, and the wording rules the app must never break.

- Tests: `node tests/run-core-tests.mjs sit-tracker-v2.html` (227/227 as of 2026-07-09 evening)
  and in-app Settings → Run self-tests or `?selftest=1`. Extend runSelfTests() with every CORE change.
- SW dev gotcha: once sw.js registers (http only), it serves the CACHED html — after editing
  the file, unregister + delete caches in the test tab, and bump SW_VERSION in sw.js for
  every real deployment or clients never see the update.
- Syntax gate: extract the <script> block and `node --check` it (done in CI-less fashion by hand).
- Run the app: open file directly or `python -m http.server`. Storage is per-origin —
  file:// and localhost hold separate data.
- AI adapter rules: local deterministic parser is default and fallback; provider output is
  schema-validated (CORE.parseProviderResponse) and rejected if it invents values
  (e.g. conc > duration); drafts NEVER save without the explicit confirm modal; the app must
  work fully with no provider configured.
- Approved wording: "Reported light event", "You marked this experience as uncertain",
  "self-reported", "Consider discussing … with a qualified teacher".
  Forbidden: "Confirmed nimitta", "reached access concentration", "entered jhāna",
  "unlocked", "the AI verified your state". Self-tests grep CORE label strings for these.
- Insights are computed by deterministic CORE code only; every insight exposes range, n,
  metric, strength; no causal language; min sample sizes (5/bucket, 10 for trends).
