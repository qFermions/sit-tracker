# PROJECT_STATE — Sit Tracker

*A future session should be able to resume from this file alone.*
*Last verified: 2026-08-18, practice-training run (sections below dated as verified).*

## Practice-training run (v4.4.0, 2026-08-18) — the app becomes a training cockpit

Mission: evolve timer+journal into a quiet cockpit for the owner's actual
practice (natural breath at the nostril rim / upper lip), with sourced teaching
and zero new gamification. Design decisions + evidence:
`docs/design/practice-training-design.md`; source ledger: `PRACTICE_SOURCES.md`
(ships beside the app, SW-precached, readable from Learn).

- **Practice modes (schema v6).** `CORE.PRACTICE_MODES` — one real mode,
  `nostril_breath` (objects nostril+upperlip), with sourced instruction/cues.
  Sessions gain nullable `practiceMode`, `contactWhere`, `breathSubtle`,
  `pleasantFeeling`; v5→v6 migration nulls them on old records; CSV + import/
  export round-trip tested. DATA_CONTRACT.md updated (authoritative).
- **One-tap start.** `settings.sitConfig` remembers the full sit configuration
  on every Start and re-arms it at boot; Today leads with a Current-practice
  card (mode, saved config, object line, last sit + owner's own last note
  excerpt — continuity, no levels/scores/predictions).
- **The sit is a fact.** Timer completions save immediately (minimal honest
  record incl. practiceMode stamp); the review opens as enrichment of the
  saved entry ("Close — sit is saved"); reset still discards. Three new one-tap
  reflection rows (breath clearest at / became subtle / pleasant feeling —
  yes/no/not sure), all nullable.
- **Orb demoted during the sit** (design §12, option D): settle animation only
  during the prep countdown (`body.settling`); static dim disc while running —
  the practice object is the breath, not the screen.
- **Learn rebuilt.** Source map = four distinct tradition cards (what MN 118
  itself says — and does NOT specify; Pa-Auk; Brasington; Thai Forest), a
  "Jhāna, honestly" module with the boundary sentence ("The app records your
  practice. It does not decide what meditative state you attained"), and 8
  troubleshooting cards that preserve genuine tradition disagreements (subtle
  breath, lights) instead of averaging them. The old "every source says the
  same" lights card was removed as fake consensus. All content lives in CORE
  structures (`PRACTICE_SOURCE_MAP`, `JHANA_MODULE`, `TROUBLESHOOTING`) so
  tests hold every card to a source + label. In-app content is attributed
  summary, not quotation (direct fetches were proxy-blocked; verification
  method recorded in PRACTICE_SOURCES.md).
- **Progress.** Three new deterministic questions (focus-point distribution,
  subtle-breath frequency with answered-question denominators, own-notes
  replay after highest-ratio sits) under the same range/n/strength honesty
  contract.
- **Gates (all exercised 2026-08-18):** node suite **447/447** (394→447);
  payload 341,771 bytes under the ADR-0003 ceiling 344,064 (ceiling + SW/app
  version match now machine-enforced by tests/run-core-tests.mjs); SW v4.4.0
  precaches PRACTICE_SOURCES.md; browser pass 34/34 in Playwright-driven
  Chromium at 390×844 (hero→skip→one-tap start→markers→pause→finish→auto-save
  →reflections→reload re-arm→Learn incl. in-app ledger→Progress honesty→
  offline reload from SW→responsive sweep 360/390/844×390/768, zero console
  errors after adding the missing favicon link); file:// double-click
  self-tests 447/447 in-DOM. Real phone hardware still untested (unchanged
  limitation). Fresh-context review: see section below.

## Current practice position

- **Gate 0 — Foundation.** 30 minutes daily at the nostril rim / upper lip; count cycles
  1–8, restart; return without commentary; when the breath goes faint, wait.
- 30-day unbroken streak before booking the first retreat. Progress shows n/30 plus the
  descriptive "days sat, last 30".
- The owner's first real sit is imminent/logged — **treat any browser localStorage as
  production data.** Verification always happens on a throwaway localhost origin.

## App version & schema

- App **v4.4.0** (`CORE.APP_VERSION`), SW cache **v4.4.0** (`sw.js` SW_VERSION — ⚠ bump on
  every HTML edit or installed clients keep the stale shell; the version match is now
  machine-enforced by the test runner).
- **Data schema v6** in envelope `jhanaTracker.v2` — see DATA_CONTRACT.md (authoritative).
  v6 adds nullable session `practiceMode`/`contactWhere`/`breathSubtle`/`pleasantFeeling`;
  migration chain v1→v6 tested end to end (older records get nulls, never guesses).
- `nimitta` and `aiConfidence` stored names remain permanent.

## Product shape (v4.0.0 family-beta + 2026-07-10 depth run)

- **Five tabs:** Today · Journal · Progress · Learn · Settings. Onboarding, Today home
  (status strip + cinematic timer + preset cards), quick log, demo isolation, local-only
  feedback, install guide — all as shipped in v4.0.0 (see git history for details).
- **Timeline from markers (new):** the review timeline pre-fills from the one-tap in-sit
  markers via `CORE.timelineFromMarkers` (documented convention: steady→mostly steady,
  wandering→wandering, returned→intermittent, dull/agitated→themselves, notable=event
  only; pre-first-marker span is wandering after a wandering/returned first tap, else
  uncertain). Visible "suggested from your in-sit markers" notice; any hand edit flips
  `timelineSource` to 'manual'; the manual contact estimate always wins; nulls stay null.
- **Deterministic insights (new):** Progress has "Ask about your practice" — four canned
  questions answered instantly by CORE (`answerQuestion`): what precedes low-ratio
  sessions (preceding day-gap comparison, bottom tercile vs rest), most frequent
  hindrance, ratio by time of day, settling trend. Every answer carries range, n, metric,
  strength (weak/moderate/reasonably supported/insufficient); hard minimum samples; no
  causal wording (tested). The passive Observations list reuses the same functions.
- **Journal parser round 2 (new):** word-number compounds (twenty-two / thirty five),
  ranges → midpoint + confidence downgrade ('15 or 20', '8 to 10', digit '25-30'),
  clock start-times (hh:mm am/pm, quarter/half past, quarter to; ambiguous bare hours
  become clarifying questions, never guesses), clause-scoped negation ("no restlessness"
  records nothing; "not strong" can't mark strong), "didn't wander" → 0.
- **Provider mock harness (new):** `CORE.MOCK_PROVIDER_RESPONSES` +
  `AI.runMockContract()` exercise the full adapter contract (valid Anthropic/OpenAI,
  malformed, refusal, overclaim, timeout) with no key and no network; failures fall back
  to the local parser with honest messages (`CORE.providerErrorSummary`).
- **Teacher workflow v2 (new):** flag-any-session with a private note from the session
  detail modal (`CORE.nextReviewStateOnFlag`: none→flagged only; never downgrades;
  code can never set 'reviewed'). Teacher report: options dialog (30/90/custom range,
  notes column toggle), flagged appendix with private notes, ⚑ row marks, neutral
  unusual-experience summary (`CORE.unusualExperienceSummary`).
- **Learn build-out (new):** structured summaries from the two practice documents under
  progressive disclosure — sit script, SN 51.20 energy tuning, if-a-light-appears first;
  the wider classical map with per-stage epistemic badges ('scientific finding' added to
  the legend; the powers marked "no verified case in recorded history"); in-app viewers
  show the unaltered .md sources (also cached by the SW for offline).
- **Bilingual scaffold (new):** `CORE.I18N` — English defaults, empty Burmese slots the
  owner fills by hand (machine translation forbidden); `tr()` falls back to English;
  the Settings language toggle appears only once ≥1 screen is fully translated
  (`fullyTranslatedScreens`), so the app ships English-active with the toggle hidden.
- **Data longevity (new):** exports stamped `-YYYYMMDD-HHMM`; storage health leads with
  the age of the last backup (highlighted >14 days / never); README documents the
  recovery procedure; restore rehearsal is CORE-tested (field-level equality) and was
  performed live in a clean context this run.

## How-to-use guide (2026-07-12 afternoon, explicit feature order for hand-off night)

- **v4.3.0.** One addition under an explicit override of the no-new-features rule: a
  "How to use" guide that teaches operating the app only — never meditation, never
  claims. Copy lives in `CORE.GUIDE` (7 sections: start/end a sit, the self-reported
  log, history, share card, teacher report, export/import + "everything stays on this
  phone; nothing is uploaded anywhere", home-screen install).
- **Placement:** a "how to use →" pill first in Today's utility row — one tap from home,
  opens a standard dialog, never blocks anything, sit screen untouched. First-run
  prominence = an accent border on the pill until first opened; `settings.guideSeen`
  remembers dismissal (survives the migrate round-trip, tested). Reuses existing pill +
  dialog styles; zero new CSS.
- **Gates:** file 302,929 → 306,367 bytes (833 under the 307,200 ceiling); tests
  387→394 (guide existence/topics, data-locality sentence, no teaching/attainment/
  clinical/streak language by regex, dismissal persistence, and structural exclusion —
  guide copy provably absent from the envelope, CSV, and share lines); teacher-report
  exclusion holds structurally (report renders only session fields). Both suites
  394/394; console clean; dialog verified at 390-wide (349px, 7 sections, no overflow).
- **Delivery:** dist/ + sit-tracker-v4.3.0.zip rebuilt; the room URL
  (192.168.1.231:8080) confirmed serving the new bytes and SW v4.3.0. Phones that
  installed v4.2.0 pick up the update notice on their next online open. The verified
  v4.2.0 zip remains as fallback.

## Release verification (2026-07-12, evening hand-off)

Verified with tool evidence on this date, at 823dbf2 / v4.2.0 unchanged:
- node CORE suite 387/387; in-app 387/387 over http with exactly one console message;
  **file:// double-click path proven** (headless Chrome, in-DOM "CORE self-tests:
  387/387 passed ✓"); **offline reload proven live** (server killed → shell, self-tests,
  and the Burmese Learn documents all served from the SW cache).
- SW/manifest internally consistent: all 8 precached assets exist on disk and match the
  runtime file set; manifest icons present; start_url/scope/display correct.
- Export→restore rehearsed again across throwaway origins: field-level equality,
  re-import 0 fresh / 2 duplicates. Teacher report generated during the pass contained
  no `[TEST DATA]` entries.
- Network audit during a full exercise pass (all tabs, share card, invite): only
  same-origin requests — zero external calls.
- **Hand-off bundle**: `dist/` + `sit-tracker-v4.2.0.zip` (153,800 bytes) with the 8
  runtime files + INSTALL.md (invite voice, LAN address 192.168.1.231, no links).
  Note: the two abhinna .md docs are IN the bundle deliberately — the SW precache list
  includes them and `cache.addAll` fails wholesale if any asset 404s. The bundle was
  served and booted from `dist/` before zipping: 387/387, SW installed, 8/8 precached.
- Still only provable on real glass: rendering quality, install prompts, screen reader.

## Visual identity + friend-facing layer (2026-07-11 run)

- **Identity system** (documented in ARCHITECTURE.md): one `:root` token layer — brave
  display type from the system stack (zero font bytes), midnight palette with an
  AA-audited text ramp (all pairs ≥4.65:1, spot-audit recorded in the run), three
  elevation levels + one glass recipe, exactly three gradients, 120/220/480ms motion
  with press-scale/hover-lift, pill radius language. No idle animation loops anywhere;
  `prefers-reduced-motion` kills everything (global rule).
- **Surfaces:** first-open hero (name treatment, one-line promise, finite-breathing orb,
  single Begin action) → existing 3-screen intro; Today = signature screen (three stat
  tiles with display numerals + teal done-state, hero timer card, oversized gradient
  CTA); Progress (identity chart palette, personality empty state); History entry cards
  (minute anchor + meta + truncated note); Learn 64ch editorial measure; glass dialogs +
  toast; segmented pill tab bar; icon/manifest refreshed (orb-glow ring, #0a0e15).
  **The sit screen was exempt** — palette inheritance only, no new motion or decoration.
- **Friend-facing:** canvas share card (story/square, orb motif, "N minutes · day M" +
  date + 'self-reported practice record'; saved manually, never posted; CORE-tested data
  assembly excludes demo/test and yields null on an empty log) from session detail or
  Progress; copyable invite text in the product voice (CORE-tested: no links, no
  attainment language); demo card recopy ("Try the demo").
- **Bugs found by this pass:** `<dialog>` was left-anchored (universal margin reset beat
  the UA's `margin:auto`) — fixed; segmented tab bar overflowed 360/390 viewports — fixed
  (viewport sweep clean at 360 / 390×844 / 844×390 / 768 / 1280 across all five tabs).
- **Performance:** file 285,138 → 302,929 bytes (+17.8 KB); icons +36.0 KB; total pass
  growth ≈ +53.8 KB against a ≤300 KB budget; zero embedded fonts; domInteractive ≈102 ms
  served locally; no idle animation loops (frame-drop sampling was not possible in this
  environment — the automation window was hidden; animations are CSS transform/opacity
  only).

## Verification record (2026-07-10 depth run)

Suite counts after the 2026-07-11 visual run: **387/387** node and in-app (375 + 12 new:
share-card data assembly ×8, invite text ×4). Clean load: one console message.

- `node tests/run-core-tests.mjs sit-tracker-v2.html` → 375/375 at that date (271 + 104
  new: timeline-from-markers ×20, v4→v5 migration ×3, insights/questions ×20, parser
  round 2 ×31, provider fixtures/summaries ×9, teacher rules ×9, i18n ×9, restore
  round-trip ×1, plus supporting assertions).
- In-app `?selftest=1` → **375/375**, exactly one app console message (the self-test
  log) — zero errors on clean load.
- Live Chrome (throwaway localhost origins): marker-suggested timeline pre-fill → save →
  provenance 'markers'; hand edit → 'manual', divergence notice, manual wins; envelope
  v4→v5 migration on existing data; Ask-a-question card with honest insufficient-data
  answers; `AI.runMockContract()` — all four failure modes fell back with honest
  messages; flag dialog persisted state + note; report v2 rendered range header,
  appendix, ⚑, honesty footer, notes-column toggle; Learn viewers loaded unaltered
  documents with Burmese intact; onboarding unchanged after the i18n refactor; injected
  Burmese slot rendered (ယနေ့) while empty slots stayed English; restore rehearsal:
  2 rich sessions → clean context import → field-level equality, re-import 0 fresh /
  2 duplicates; **SW update path observed live**: v4.0.0→v4.1.0 notice → reload → old
  cache deleted, sessions intact.
- Fix this run: duration patterns didn't accept hedge words between "for" and the number
  ("sat for about twenty minutes") — caught by a new test, fixed.

## Architecture

Unchanged layering (ARCHITECTURE.md): pure CORE (now also: timelineFromMarkers, insight
question engine, i18n table, teacher rules, provider mock fixtures) · STORE · AUDIO ·
TIMER · AI · UI modules TODAY / ONBOARD / FEEDBACK / REVIEW / HISTORY / PROGRESS / MAP /
JOURNAL / SETTINGS / APP. `window.__sitTracker` exposes {CORE, STORE, TIMER, AI, REVIEW,
APP, ONBOARD, TODAY} for scripted checks. ADR-0001 stay-vanilla intact: single file +
manifest + sw.js + icons; no dependencies, no build.

## Remaining limitations (honest)

1. No web bell while the screen is locked (platform limit, stated in the UI; ADR-0002).
2. Real iOS/Android devices still untested — desktop Chrome only; A2HS, standalone
   storage isolation, and real install prompts unobserved.
3. Screen-reader testing not performed (semantics/labels/live regions in place).
4. No live AI-provider round trip (no key in this environment; the mock harness covers
   the contract, not a real provider's behavior).
5. Multiple tabs running the same sit: last-writer-wins on the timer key.
6. Burmese slots in `CORE.I18N` are all empty by design — the owner supplies them;
   the language toggle stays hidden until at least one screen is complete.
7. Print output was content-verified in DOM, not pixel-verified on paper this run.

## Family distribution (no deploy)

Serve the folder on the home network (`python -m http.server 8080`), open
`http://<computer-ip>:8080/sit-tracker-v2.html` on each phone, follow Settings →
"Install on your phone", run the offline checklist, then testers use "Load demo data"
or their own sits and send feedback via the beta chip.

## Immediate next practice action

Sit 30 minutes today; press Start on the recommended card; log it honestly. After the
sit, tap the markers you actually used — the review timeline will pre-fill itself.
