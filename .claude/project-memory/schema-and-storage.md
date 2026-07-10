Schema v3 envelope in localStorage key `jhanaTracker.v2`; stored names are permanent.

- Envelope: {schemaVersion:3, sessions[], settings{}, map, savedAt}. Timer state is a
  separate key `jhanaTracker.v2.timer` so ticking never rewrites sessions.
- Keep stored names exactly: `nimitta{category,…}` for the light/image report and
  `aiConfidence` for per-field draft evidence. Any rename = schemaVersion bump + migration
  in CORE.migrate + tests. Never rename for cosmetics.
- Legacy v1 keys `janSits`/`janGates` are read-only: migrated into the envelope once,
  NEVER written or deleted (the wipe function intentionally skips them).
- Missing values are null ("not reported"), never 0. `concMin > actualMin` must be rejected
  by validation, not silently clamped.
- Unparseable envelope bytes are quarantined under `jhanaTracker.v2.recovered-<ts>`, never discarded.
- API keys live only in localStorage settings (aiKey) — never in files or commits, and
  exportJSON strips settings.aiKey from every backup (privacy: backups get shared).
- New settings keys (2026-07-09): lastExportAt, backupSnoozeUntil (both 'YYYY-MM-DD'|null),
  consumed by CORE.backupStatus for the calm export reminder.
- Full persisted-field contract lives in DATA_CONTRACT.md — update it with any schema change.
