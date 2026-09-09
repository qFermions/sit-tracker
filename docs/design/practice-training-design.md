# Practice-training design note (v4.4.0 run, 2026-08-18)

Evidence base: repository state at fcd0e55 (v4.3.0, schema v5, 394 tests); product
research on Insight Timer / Waking Up / Headspace / Balance (help-center docs +
reviews, accessed 2026-08-18); meditation-source research recorded in
`PRACTICE_SOURCES.md`. This note decides; the ledger cites.

## What this release is

Turn the app from "timer + journal" into a quiet cockpit for ONE practice the
owner is actually training: **natural breath, attention at the nostril rim /
upper-lip contact area**. Less setup, less on-screen during the sit, a faster
honest record afterwards, and a Learn tab that teaches the current method and
names its sources instead of implying one universal doctrine.

## Before a sit — one tap to the cushion

Research: the strongest timer products make a *saved configuration* the unit of
starting (Insight Timer presets), attach the only real decision (duration) to
the start moment, and are eroded by config friction (top review complaint).
Today's app forgets everything between visits: preset resets to "first",
bells reset to defaults every load.

Decisions:
1. **Current-practice card** at the top of Today: names the practice
   (from `CORE.PRACTICE_MODES`), its object cue in one line, the saved duration
   and bells, and one Start action. Opening the app → pressing Start is the
   entire flow.
2. **The app remembers the last-used sit configuration** (duration/preset,
   settling countdown, bells, wake-lock, focus point) in
   `settings.sitConfig`, written on every timer start. No new configuration
   surface — the existing Options panel is now simply persistent.
3. The existing preset cards remain below as alternates; the review-a-sit card
   and custom length stay.

## During a sit — the screen recedes

Research: during-sit screens in serious products are a clock at most; Headspace's
animated breathing circle is the anti-pattern for an eyes-closed tactile
practice (it recruits visual attention and assumes the phone is watched).

The current app animates the orb in an 8-second loop **for the whole running
sit**. For a nostril-sensation practice this is exactly the wrong invitation:
a continuously breathing screen object competing with the actual breath.

**Orb decision (mission §12): option D — demote the orb to a nearly static
visual during the running sit.** It keeps its settle animation during the
prep countdown (where a settling cue is plausibly useful and the eyes are
still open), then freezes to a dim static disc once the sit proper starts.
Pause keeps the existing dimmed static treatment. Not removed: it still
carries the arc and the visual identity; it just stops moving while you
meditate. `prefers-reduced-motion` continues to kill everything.

Everything else during the sit is already right and stays: remaining time,
pause/finish/reset, optional one-tap markers, "Quiet screen" zen mode, no
metrics, no prompts.

## After a sit — the sit is a fact; the reflection is optional

Research: Insight Timer auto-logs the session and makes the journal prompt
opt-in; Balance shows a single tappable question is a viable sub-10-second
reflection unit. Today's app *discards the entire sit* if the review form is
closed without saving — the record of the sit is held hostage by the form.

Decisions:
1. **Timer-completed sits save immediately** as a minimal honest record (date,
   times, planned/actual minutes, focus point, practice mode, markers,
   entrySource 'timer') the moment the final bell sounds. The review form then
   opens as an *edit* of that saved entry. "Close without saving" becomes
   "Close" — closing keeps the sit, loses nothing, and the entry can be
   enriched or deleted later like any other. Reset during a sit still discards
   (nothing was completed). Manual/AI/import flows are unchanged.
2. **Three new one-tap reflection rows** in the existing Quick impressions
   block, chosen because they are the observations the four researched
   traditions themselves treat as practice-relevant (see PRACTICE_SOURCES.md):
   - *Where was the breath clearest?* nostril rim / upper lip / both /
     elsewhere / unclear
   - *Did the breath become subtle or faint?* yes / no / not sure
   - *Pleasant bodily feeling noticed?* yes / no / not sure
   All three are nullable self-reports; a session with none recorded stays
   null (never zero, never guessed). No field is ever labeled with an
   attainment ("access concentration", "nimitta achieved" stay impossible).
   Rejected: continuity percentage sliders, per-sit gradings, any new
   required field — the form must stay ~30 seconds.

## Practice modes — a durable "what am I training"

New CORE concept, deliberately small:

```
PRACTICE_MODES: [{ id:'nostril_breath', name, object:'nostril',
  instruction, prepCue, returnCue, subtleCue, sourceIds:[…], status:'current' }]
```

One real mode this release. It exists so the app can (a) show the owner
exactly what he is training, with wording traceable to sources, (b) stamp
sessions started from it (`session.practiceMode`, nullable, v6), and (c) hold
future modes as data, not code. Educational material about *other* approaches
lives in Learn as reference, not as selectable modes — no technique shopping.

`settings.currentPracticeMode` defaults to `nostril_breath`. Sessions from
older versions keep `practiceMode: null` ("unknown", like entrySource pre-v3).

## Schema v6 (migration contract)

Adds four nullable session fields: `practiceMode`, `contactWhere`,
`breathSubtle`, `pleasantFeeling`. Migration v5→v6 sets all four to null on
existing records (missing stays missing). Envelope settings gain
`sitConfig` + `currentPracticeMode` (scalar prefs, no migration needed).
CSV gains the four columns. Export/import round-trip and the v1→v6 chain are
tested. Stored names permanent per DATA_CONTRACT.

## Learn — teach the method, name the lineage

Structure (compact cards inline; the full citation ledger is
`PRACTICE_SOURCES.md`, readable in-app via the existing document viewer and
precached by the service worker):

1. **Start here — your current practice.** Plain-language instruction for the
   nostril-breath sit: where attention rests, natural breathing, what
   "returning" means, what not to force, what to do when the breath gets
   subtle, what the practice trains. Practice-guidance badge, sources named.
2. **The source map.** Four clearly separated cards: what MN 118 itself says
   (and pointedly does NOT specify), the Pa-Auk approach, Leigh Brasington's
   approach, the Thai Forest (Ajaan Lee / Thanissaro) approach. Framing: these
   are related practices, not one doctrine. The existing "every source says
   the same" line about lights is removed as a fake consensus (the traditions
   genuinely differ; the difference is now shown).
3. **Jhāna, honestly.** What the traditional category is, where the
   researched teachers differ, and the boundary sentence rendered
   prominently: *"The app records your practice. It does not decide what
   meditative state you attained."*
4. **Troubleshooting.** Short cards: wandering, sleepiness, forcing the
   breath, breath gone faint, tense attention, pleasant sensation, lights /
   imagery, striving. Where traditions disagree (subtle breath, lights), the
   card shows per-teacher guidance instead of a synthetic average.

All substantive traditional content lives in CORE as structured data
(`PRACTICE_SOURCE_MAP`, like GUIDE) so tests can assert: every module carries
a source label, tradition cards stay distinct, and no learner-visible string
certifies attainment. Existing epistemic badges are reused; each sourced card
gets a faint "Source: …" line.

## Progress — better questions, same honesty rules

Add to the deterministic insight engine (same range/n/strength contract):
- *Which focus point am I actually using?* (object distribution, last 30)
- *How often has the breath become subtle lately?* ("In 4 of your last 7
  recorded sits…" phrasing; denominator = sits where the question was
  answered; insufficient below 5 answers)
- *What did I write after my steadiest sits?* (dates + note excerpts of the
  top-ratio tercile — the owner's own words replayed, no interpretation)

Today additionally gets a quiet **continuity line** under the current-practice
card: most recent sit + the owner's own last note excerpt. No levels, no
percentages-to-anything, no predictions. The existing descriptive streak
tiles stay as they are (mission: don't increase gamification; don't rip out
what works).

## Size ceiling

ADR-0003: ceiling raised 300 KiB → 336 KiB as a recorded tradeoff, now
machine-enforced by the test runner. Long-form content externalized to
`PRACTICE_SOURCES.md` first; inline additions budgeted ≈20–28 KB including
tests. `SW_VERSION` bumps to v4.4.0 with the HTML change; the new .md joins
the precache list.

## Explicitly rejected in this run

- Auto-detecting or scoring any meditative state (forbidden, tested).
- New gamification of any kind; guilt-framed anything.
- A field-per-tradition reflection form or >3 new post-sit fields.
- Selectable alternative practice modes this release.
- Machine-translated Burmese (owner-supplied only, unchanged).
- Removing the orb entirely (option A/B were weaker: A preserves a
  during-sit animation loop that competes with the practice object; B —
  reduce — keeps residual motion; C — a visibility toggle — adds a decision
  where the evidence says remove the decision).
