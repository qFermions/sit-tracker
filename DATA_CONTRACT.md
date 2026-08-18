# DATA_CONTRACT — persisted data, schema v6

This is the authoritative contract for any future client (iOS wrapper, sync tool).
Stored names are permanent; changes require a `schemaVersion` bump + migration + tests.

## Envelope — localStorage key `jhanaTracker.v2`
| Field | Type | Semantics |
|---|---|---|
| schemaVersion | int (6) | current schema; see version history below |
| sessions | Session[] | append-mostly log; union-merge by `id` on import |
| feedback | {at, entry, text}[] | local-only family-beta feedback reports (v4) |
| settings | object | scalar preferences, last-write-wins (see Settings) |
| map | object\|null | practice-map bookkeeping (see Map) |
| legacyGates | any? | preserved v1 `janGates` content, opaque |
| savedAt | ISO string | last save timestamp |

## Session (all "not reported" values are `null`, never 0)
| Field | Type | Null? | Semantics |
|---|---|---|---|
| id | string | no | unique; also dedup key on import (with date+startTime+actualMin fingerprint) |
| v | int | no | schema version stamp |
| date | 'YYYY-MM-DD' | no | local practice date |
| startTime / endTime | 'HH:MM' | yes | local clock times |
| plannedMin / actualMin | number | planned yes / actual no | minutes; actualMin > 0 required |
| concMin | number | yes | **self-reported** estimated minutes of genuine breath contact; must be ≤ actualMin |
| ratio | number 0–1 | yes | derived concMin/actualMin, recomputed on save |
| confidence | 'low'\|'medium'\|'high' | yes | user's confidence in concMin |
| settleMin | number | yes | self-reported minutes to first settle |
| longestSteadyMin | number | yes | self-reported; ≤ actualMin |
| wanderings / returns | number | yes | counted episodes |
| object | 'nostril'\|'upperlip'\|'abdomen'\|'wholebody'\|'custom' | yes | meditation object |
| objectCustom | string | yes | free text when object='custom' |
| posture | string | yes | free-ish ('cross-legged'…) |
| phase | string | no (default 'foundation') | practice-map phase label |
| energyBefore/After, calmBefore/After | int 1–5 | yes | self-rated scales |
| stability | int 1–5 | yes | quick-log: attention steadiness (1 scattered … 5 steady), self-rated |
| breathClarity | int 1–5 | yes | quick-log: breath clarity (1 faint … 5 clear), self-rated |
| practiceMode | string\|null | yes | (v6) id of the saved practice the sit belongs to (`nostril_breath`); any non-empty string valid for forward compatibility; null = unknown/none — never guessed |
| contactWhere | 'nostril'\|'upperlip'\|'both'\|'elsewhere'\|'unclear' | yes | (v6) where the breath was clearest, self-reported |
| breathSubtle | 'yes'\|'no'\|'notsure' | yes | (v6) whether the breath became subtle/faint at some point, self-reported; null = question not answered (≠ 'no') |
| pleasantFeeling | 'yes'\|'no'\|'notsure' | yes | (v6) whether a pleasant bodily feeling was noticed, self-reported; a neutral report, never evidence of any state |
| afterStateReport | 'calmer'\|'no change'\|'more agitated'\|'tired'\|'energized' | yes | directional self-report (journal-derived) |
| hindrances | {key→'mild'\|'moderate'\|'strong'} | no (may be {}) | keys: sensualDesire, illWill, sloth, restlessness, doubt |
| dominantHindrance | key\|null | yes | at most one |
| qualities | string[] | no (may be []) | reported qualities (placement, sustained, bodilyEnergy, ease, unification, equanimity, brightness, reducedBody, reducedSpeech, timeDistortion, other) |
| **nimitta** | object\|null | yes | **stored name is permanent.** `{category, duration?, color?, brightness?, stability?, effortChanged?, persisted?, emotion?, timing?}`; category ∈ none, uncertain, brief, flicker, unstableImage, stableImage, brightField, other. `null` = not reported (≠ 'none'). Neutral report, never a certification. |
| timeline | Segment[]\|null | yes | `{kind, startMin, endMin}`, kind ∈ wandering, intermittent, mostly, continuous, dull, agitated, uncertain; non-overlapping, within duration |
| timelineDerivedMin | number | yes | contact estimate derived from timeline weights (documented convention: 1/.75/.35/0) |
| manualOverride | bool | no | true when saved concMin differs >0.5 from timelineDerivedMin |
| timelineSource | 'manual'\|'markers'\|null | yes | provenance (v5): 'markers' = suggested from in-sit taps and left unedited; 'manual' = hand-entered or edited; null = no timeline |
| markers | {atMin, kind}[]\|null | yes | live one-tap markers; kind ∈ steady, wandering, returned, dull, agitated, notable |
| notes | string | no (may be '') | user notes |
| journalText | string | yes | verbatim original journal text (AI-drafted sessions) |
| **aiConfidence** | object\|null | yes | **stored name is permanent.** Per-field `{value, confidence, evidence}` extraction provenance for AI-drafted sessions |
| entrySource | 'timer'\|'manual'\|'ai'\|'imported'\|null | yes | null = unknown (pre-v3 data) |
| teacherReview | 'none'\|'flagged'\|'discussed'\|'reviewed' | no | only the user may set 'reviewed' |
| teacherNotes | string | yes | private notes from teacher conversations |
| createdAt / updatedAt | ISO string | yes | audit timestamps |
| _test | true? | absent on real data | synthetic marker; notes also start with `[TEST DATA]`. Synthetic entries are excluded from statistics, streaks, backups/exports, and the teacher report |
| _demo | true? | absent on real data | friendly demo-data variant of _test |
| _legacy | object? | absent normally | original v1 record preserved through migration |

## Settings (scalar, last-write-wins)
`aiEnabled` bool · `aiEndpoint` string · `aiModel` string · `aiKey` string (plain text,
local only; **stripped from every JSON export** — a restored backup requires re-entering the key) ·
`bellVolume` 0–100 · `lastExportAt` 'YYYY-MM-DD'|null · `backupSnoozeUntil` 'YYYY-MM-DD'|null ·
`onboarding` {done:bool, step:int} (first-launch introduction state, v4) ·
`language` 'en'|'my' (default 'en'; Burmese strings are owner-supplied in `CORE.I18N`,
never machine-translated; the toggle only appears once ≥1 screen is fully translated) ·
`guideSeen` bool · `currentPracticeMode` string (v6, default 'nostril_breath') ·
`sitConfig` object|null (v6, last-used sit configuration — see version history).

## Map
`{currentLevel: 0–5, levels: [{evidence, teacherNotes, reviewDate}] ×6}` with evidence ∈
not-assessed, self-reported, repeated-pattern, discussed, teacher-reviewed (never auto-set).

## Timer key `jhanaTracker.v2.timer`
`{core: {phase, plannedSec, prepSec, startMs, pausedAtMs, pausedTotalMs}, ctx: {date,
startTime, plannedMin, object, objectCustom, markers[], bellsEverySec, finalBell,
wantWakeLock}}` — transient; cleared on completion/reset; elapsed is always derived from
timestamps, never stored.

## Schema version history
- **v1** (legacy): loose keys `janSits` (array of sits, tolerant field mapping:
  minutes/min/duration → actualMin, focusMinutes/focus/conc → concMin) and `janGates`.
  Migrated once into a fresh envelope; original keys never touched.
- **v2**: envelope without entrySource / teacherReview / afterStateReport / markers / teacherNotes.
- **v3** (2026-07-09): adds those five fields; unknown entrySource stays null.
- **v4** (2026-07-09 beta run): adds session `stability` + `breathClarity` (null = not
  reported), envelope `feedback[]`, settings `onboarding`. JSON exports exclude synthetic
  entries and the AI key.
- **v5** (2026-07-10 depth run): adds session `timelineSource` provenance;
  migration marks every pre-v5 timeline `'manual'` (they were all hand-entered), else null.
- **v6** (current, 2026-08-18 practice-training run): adds session `practiceMode`,
  `contactWhere`, `breathSubtle`, `pleasantFeeling` — all null on migrated records
  (missing stays missing). CSV gains the four columns. New scalar settings (no
  migration needed): `currentPracticeMode` (default `nostril_breath`) and
  `sitConfig` `{min, prepSec, intervalMin, finalBell, wantWakeLock, object,
  objectCustom}` — the last-used sit configuration, rewritten on every timer start.

## Sync contract (two devices, no accounts)
Transport = the JSON export file (user's own cloud folder). Merge = union by session `id` +
duplicate fingerprint (date|startTime|roundedMinutes); imports never overwrite existing
sessions; settings do not merge (device-local). The export file is transport, not truth.
