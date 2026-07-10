# IMPLEMENTATION_PLAN — Sit Tracker

*Architecture decisions and roadmap. Current status lives in `PROJECT_STATE.md`.*

## Fixed decisions (do not re-litigate)

1. **One file** (`sit-tracker-v2.html`), vanilla JS, zero dependencies, no build system.
   Double-click-and-run and offline operation are product features.
2. **Storage**: versioned envelope in localStorage (`jhanaTracker.v2`) behind a small
   adapter. IndexedDB migration only if a concrete defect appears that the adapter cannot fix.
3. **Pure CORE block** between `/*CORE-START*/` and `/*CORE-END*/` — everything testable
   under Node lives there. UI modules never contain business rules.
4. **Deterministic-first AI**: the local parser is the default engine; an external provider
   is an optional, schema-validated, fallback-guarded enhancement — never a requirement.
5. **Evidence rule**: the app records self-reports; it never certifies attainment. Forbidden
   wording ("confirmed nimitta", "unlocked", "you entered jhāna", "verified your state") is
   guarded by self-tests.
6. **Schema discipline**: stored names are permanent (`nimitta`, `aiConfidence`, …).
   Changes = schemaVersion bump + migration + tests.

## Build phases (all complete as of 2026-07-09)

1. Data safety: envelope, migrations (v1 legacy → v3), export/import/CSV, corruption quarantine.
2. Timer: timestamp math in CORE, persistence, refresh/sleep recovery, bells, wake-lock, zen mode.
3. Markers → 4. Review → 5. Hindrances/qualities → 6. Neutral nimitta reporting →
7. Journal AI (local parser + provider adapter) → 8. Progress dashboard → 9. Deterministic
insights → 10. History → 11. Practice map → 12. Docs → 13. Design pass → 14. Tests (207) →
15. Live browser verification.

## Possible future work (unscheduled, in priority order)

- Auto-suggest timeline segments from in-sit markers (wandering marker → wandering segment).
- Custom date-range picker on Progress (CORE.filterRange already supports {from,to}).
- Optional gentle reminder using the Notifications API (local only, no services).
- Voice dictation into the journal via the Web Speech API where supported.
- If session count grows past a few thousand: paginate history further and consider
  IndexedDB behind the existing adapter interface.

## Testing contract

- Every CORE change extends `runSelfTests()` in the same commit.
- Both runners must stay green: `node tests/run-core-tests.mjs sit-tracker-v2.html`
  and in-app `?selftest=1`.
- "Build passes" for this stack means: the file opens with zero console errors.
