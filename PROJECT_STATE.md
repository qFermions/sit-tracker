# PROJECT_STATE — Sit Tracker

*A future session should be able to resume from this file alone.*
*Last verified: 2026-08-26, Apple design pass (sections below dated as verified).*

## Night Practice + Apple restraint (v4.6.0, 2026-09-09) — the sit leads, the update window closes

**Tested implementation `c23a0a5`** (initial `7fe2434`, corrected after independent review; manifest commit
`d44ec17`; documentation commits follow and are not the tested implementation). App 4.6.0 = SW v4.6.0, schema 6, data keys unchanged.
`sit-tracker-v2.html` 339,746 B sha256 `8af95fbf5fa7350aa48b7825b116c598dbc422abcbc4ff6ef01e3a0afa406fbf`;
payload xz sha256 `54cf7de69dc1d6233f1220001b79403fedee2f55549baaa9b17a345435ba3f63` (ADR-0003 ceiling
344,064 unchanged; headroom 6 → 4,318 — the redesign reclaimed bytes).
Direction and measured tokens: `APPLE_DESIGN_SYSTEM.md` Part 0. HIG-inspired; not an Apple
certification. Previous artifact (ec9b564, v4.5.0) and its bundle/receipts preserved for rollback.

Three largest design failures found in the BEFORE renders and what changed:
1. **Start was below the fold at every width** (header chip, backup notice, practice card, three
   stat tiles and three pills came first). Now the orb, the time and one dominant Start action open
   Today; the remembered practice, its configuration and one continuity line follow, then presets.
2. **Card-around-everything on a cool-blue dashboard palette.** Now one consolidated token layer:
   near-black ground, flat charcoal surfaces with a single edge, warm labels, restrained amber; light
   is warm paper + ink + brown-amber, calibrated separately. No gradients, glows or drop shadows.
   Journal history is a list, Learn an editorial page, Settings grouped lists with capital headers,
   the tab bar translucent over content with an opaque fallback under reduced transparency.
3. **The active sit was cluttered and fractured** ("Wandering" broke mid-word). Markers sit in a
   grid that never fractures; the stage is open ground; Reset and Quiet Screen are quiet ghosts;
   the orb still settles with you and holds still during the sit.
Removed from Today: stat tiles, the "works offline" pill, the header beta chip (feedback stays in
Settings; how-to-use and install remain as links). No feature removed.

**Mixed-version window — reproduced, then closed (in scope this pass).** With the real v4.5.0
output installed from its start_url (never "/"), an active sit and a second tab, deploying v4.6.0
and opening "/" ran the new document under the old worker (both caches present) — reproduced.
Fix, two parts: the worker answers a navigation to the scope root or to the app document (any
query) with its own cached copy, so a page can never run a newer or older document than the worker
serving it — every other navigation (a companion .md opened directly, an icon, an unknown path)
keeps its cache-first answer and its real 404; and `migrate()` upgrades records stamped by an older
schema even in a current envelope (a simulated older-client write came back `v:6` with the v6
fields null). In the window the new document's own registration check finds the matching worker
and offers it through the existing notice — no forced reload, the sit untouched; applying the
update moved all three tabs onto v4.6.0 with only its cache left and the sit offered back. Forward
closure is proven with a gate that can fail: a fresh start_url-only client opening "/" for the
first time while a v9.9.9 fixture sits on the network still runs v4.6.0 (a worker with the branch
stripped fails that gate), and the newer release is still offered through the notice.

**Gates on the packaged v4.6.0 directory (`dist/release-v4.6.0/public`)** — release gates 82/82
(served identity; v4.3.0/schema-5 client → v4.6.0 with records + active sit; failed precache never
replaces a usable install; export→import across two origins with duplicate policy, invalid and
future-schema input, no API key; mixed-version window and forward closure; companion documents
and unknown paths keep their own answers under the worker; offline with the server refusing every
connection and every asset byte-compared to the release; persistence; 390/1280 overflow; zero
foreign requests; zero candidate console errors) · cache-wipe mutant still fails 5 gates with
exit 1 · browser gates 49/49 (contrast in both appearances, 44×44 targets, 150 %/200 % zoom sweep,
nine widths, reduced motion, orb contract, export key-stripping) · interaction flow 35/35 (real
10 s settle + 11 s sit, pause/resume, export → wipe → import, offline reload) · core 447/447 with
ceiling/version/syntax/attribute gates · `release.mjs` check PASS, selftest 15/15; the manifest
packed from the committed tree reproduces the same digests.
Evidence: before/after screenshots (phone 390 dark+light, wide 1024) and the contact sheet,
a 390×844 real-browser walkthrough video, and every log — in the v4.6.0 private bundle.

- Independent review (Codex CLI absent — that cross-model gate stays unfulfilled; fresh-context
  Claude reviewer, job `a0925475260b6a617`, isolated worktree, ran the gates, two mutants, its own
  sweep and probes, looked at the renders). Initial verdict on `7fe2434`: **BLOCKED — 3 MAJOR, no
  data loss**: the navigation handler masked every in-scope navigation (companion documents,
  manifest, icons, 404s all returned the app); the forward-closure gate was vacuous (marker outside
  `documentElement`, "/" pre-cached — the suite stayed green with the handler deleted) and the
  `reg.update()` guard was redundant; the phase line sat under a notched phone's status bar during
  a sit because the header, the only safe-area carrier, is hidden then. Plus MINORs ("1 days",
  timer weight vs the record, navy theme-color, wordmark fracture at 200 %, 1 h+ timer at 320 px,
  Progress empty-state copy, hero focus ring, cross-tab last-writer-wins). All MAJORs and the first
  five MINORs closed at `c23a0a5` (details: `~/sit-tracker-vercel-staging/review-v4.6.0-*.md`);
  the last three stay recorded below. **Re-review 1 of 2 on `c23a0a5`: PASS** — every MAJOR fix
  reproduced by the reviewer (navigation sweep; closure gate failing on the nav mutant, 82/82 on
  the real artifact; safe-area geometry under a CDP inset override), MINORs spot-checked, identity
  confirmed. Re-review 2 unused (no code changed after `c23a0a5`). Counters: initial 1/1, re-reviews
  1 of 2, correction loop 1 of 3 (one attempt). Records: `~/sit-tracker-vercel-staging/review-v4.6.0-*.md`.
- Reviewer-noted items left as they are (pre-existing, MINOR): the Progress empty state shows dash
  tiles and the practice map's "Gate 0 target … 0/30" line (product copy — the owner's call whether
  to soften it); the first-open hero button renders a focus ring in headless Chromium (device
  behaviour unverified); saving from an old-version tab after a new tab wrote is last-writer-wins
  (limitation 5, unchanged).
- Live deployment: no Vercel probe was made (no new evidence since the 2026-09-08 wall); LIVE:
  UNPROVEN. v4.6.0 parts are packed and unsent; resume from tp_00 with the v4.6.0 manifest only.
- Unobserved and therefore unproven: real iPhone/Android installation and lock-screen behaviour,
  VoiceOver, Burmese owner approval of any copy (no copy changed).

## Release recovery + data-safety gates (2026-09-08) — the v4.5.0 artifact becomes reproducible

**Runtime artifact unchanged.** Tested revision for the runtime files: `ec9b564` (PR #2 head;
`sit-tracker-v2.html` sha256 `1b9b6abdeaf1f160dfb72c8cdc3bb1d9216701d5dd8a5daae0ae39a956a0c4e8`).
Release tooling and gates: implementation `2a3542a`, corrected after independent review at
`3dd6c1e`, test-validity MINORs closed at `ce34d0e` = the final tested implementation
(documentation commits come after it and are not the tested implementation). Procedure:
`release/README.md`. Deployment state and resume plan: `~/sit-tracker-vercel-staging/DEPLOY-STATE.md`
(outside the repo; private).

- `tools/release.mjs` — `pack` (deterministic tar+xz of the seven allowlisted source members →
  seven base64 text parts + a manifest with every full SHA-256), `check` (rebuilds in a temp dir:
  parts in manifest order bound to name + text digest + decoded digest → payload digests →
  archive safety (regular members only, declared paths only, no escapes) → source parity →
  version coherence → icons regenerated byte-identically by `tools/make-icons.mjs` → runtime
  directory is exactly the ten-file allowlist; publishes atomically, keeps the previous output;
  exit 1 on the first failed gate), `selftest` (15 fixtures: missing / duplicate / out-of-order /
  truncated / invalid base64 / validly-encoded corruption with and without a forged text digest /
  wrong expected payload, source and icon digests / undeclared output file / unreferenced extra
  file / two resume-plan fixtures — every corruption fails at the named gate and the known-good
  output is never disturbed), `resume-plan` (a part is skipped only on a receipt for this exact
  release, carrying the manifest digest, marked verified — a created deployment is not a passed
  check; a final deployment that exists but is unverified yields "verify-first", never a blind
  duplicate). A fresh pack on 2026-09-08 reproduced the August-28 parts and payload digest exactly.
- `tests/run-release-gates.mjs` — 62 gates on the ASSEMBLED release directory served as hosting
  serves it (`/` → app, revalidating SW, unknown paths 404 — properties of the test's own
  hosting-shaped server; the real host is a live gate), two isolated origins, synthetic data:
  served identity (bytes on the wire = release bytes; PROJECT_STATE.md, tests, tools, .git,
  manifest all 404); an installed **v4.3.0 / schema-5 client — what master serves** — with three
  records and a running sit receives the candidate through the app's own update notice
  (cache-first keeps the old app until the user applies; the candidate precached all nine assets
  first; apply → reload into 4.5.0; envelope migrated to schema 6 with every record and the
  device-local API key intact, v6 fields null; stale cache dropped; the sit survives with the same
  start timestamp and the app offers to continue it; with the candidate installed and waiting a
  reload still serves the old app and re-offers the notice); a candidate whose precache 404s
  never replaces the usable installation (no notice, same controller, records intact; the
  attempted install is proven by the empty cache it leaves under its own name — `Cache.addAll`
  is atomic — which the next successful activate deletes); export on origin A → import on origin B
  (contract-field parity, schema-6 stamps, no `aiKey` field or value anywhere in the backup, the
  same file twice adds nothing, invalid JSON and an unrecognised envelope are refused without
  loss, a future-schema backup merges only its new valid record, a future-schema envelope already
  on the device is loaded without destroying records or unknown fields and is not downgraded);
  under service-worker control, with the test server refusing every connection, a NEW page at the
  root URL opens with records, journal and all runtime assets and the server served nothing (the
  one attempted request — the browser's worker-script update check — was refused; Playwright's
  `setOffline` alone does not cut a worker's fetches, which the initial review proved); reload
  keeps every record exactly once; no horizontal overflow at 390 and
  1280 px; every one of the observed requests stayed on the two test origins; zero console
  errors from the candidate (the only 404 was the old v4.3.0 client's `favicon.ico` — it has no
  icon link; the candidate does).
- Existing suites on the release directory (not the source tree): core 447/447 with all gates,
  browser gates 49/49, interaction flow 35/35 (real 10 s settle + 11 s sit, pause/resume, export →
  wipe → import through the real file input, offline reload).
- Live deployment: **BLOCKED — unchanged access wall.** Two bounded reads with the saved
  identifiers (`get_project sit-tracker-preview`, `get_deployment dpl_GXLoRTm7…`, team
  `team_q5u0Ro6D8zGh5H19URVl922o`) returned 404 at ~16:51Z, as on 2026-08-28; no mutation was
  retried. LIVE: UNPROVEN. The one part already sent (tp_00) stays **unverified** in
  `receipts.json` and is resent by the resume plan.
- Independent review: Codex CLI is not installed in this environment (that bridge: BLOCKED). A
  fresh-context read-only Claude reviewer (job `aeea85c99119dd630`, isolated worktree, inspected
  `git archive 2a3542a`, ran pack/check/selftest, the full gate file and its own probes) returned
  **BLOCKED — 2 MAJOR, 0 BLOCKER**: (1) the tar pinned order/owner/mtime/format but not member
  mode, so a repack under another umask changed the release identity (reproduced: 664-mode tree
  → different xz digest; `--mode=0644` restores the committed digest); (2) the offline gates could
  pass with an empty cache because `setOffline` does not reach worker fetches (reproduced: caches
  deleted + setOffline → page still loaded with 2 server hits). MINOR: `check --publish` failed
  with EXDEV across filesystems (safe-fail); the cache-first assertion sat before the candidate
  was installed; the failed-precache leftover is an empty cache, not partial, and was a note not
  an assertion; the served-identity section proves the test's server, not the host; trust-model
  header wanted. Clean: corruption-to-output, data loss/duplication, secrets, resume/receipts.
  All of the above corrected at `3dd6c1e` (pack from 664- and 600-mode trees reproduces the
  committed digests; offline section asserts zero served bytes with the server refusing every
  connection; gates 62/62). **Re-review 1 of 2 on `3dd6c1e`: PASS** — the reviewer repacked
  from 664- and 600-mode trees (committed digests reproduced), ran the suite (62/62) and a
  cache-wiped mutant (FAIL, exit 1 — the offline gate can now fail), and confirmed the EXDEV,
  cache-first and failed-precache fixes. Two MINOR test items remained (the per-asset offline
  check was status-only because the worker answers any failed fetch with the HTML at 200; an
  offline page that fails to open threw instead of failing cleanly) — closed at `ce34d0e`: each
  asset's bytes are now compared against the release digests, and guarded probes give clean
  FAILs (mutant: 5 FAILs, summary, exit 1; real run 62/62). **Re-review 2 of 2 on `ce34d0e`:
  PASS** — the reviewer confirmed the diff touches only the offline section, reran the suite
  (62/62, all six offline assets are release bytes, 0 served) and the mutant (5 clean FAILs,
  exit 1); still open and non-blocking: this document's staleness (closed here), the pre-existing
  mixed-version design item (limitation 8), and the live host (unverifiable). Counters: initial
  review 1/1; re-reviews 2 of 2 used; correction loops 2 of 3 (one attempt each). Review
  records: `~/sit-tracker-vercel-staging/review-*.md` and the private bundle.
- Pre-existing app-design finding from the review (not introduced here, not fixed here because it
  needs an HTML/SW change and a new artifact): an installed old client that opens the root URL
  under its old worker after a deploy fetches the NEW document into the OLD cache and runs it under
  the old worker until the update is applied; `start_url` still serves the old document. Records
  are never lost, but sessions written in that window carry stale `v` stamps and `undefined`
  instead of `null` for v6 fields (tolerated by validation and CSV). Recorded under limitations.

Real-device limitations unchanged: no phone hardware, no lock-screen behaviour, no Burmese
approval observed.

## Apple design pass (v4.5.0, 2026-08-26) — the app gets a coherent, accessible surface

Mission: make Sit Tracker feel as calm, coherent and native-quality as an excellent
first-party application, while keeping its meditation identity and its deliberately
small offline architecture. Audited against a pinned third-party HIG-derived guideline
corpus (`APPLE_SKILL_PROVENANCE.md` — **not** an Apple certification, and none is
claimed).

**Documents produced:** `APPLE_SKILL_PROVENANCE.md`, `APPLE_HIG_APPLICABILITY_MATRIX.md`
(all 53 guideline docs classified, each with a reason verified against the code),
`APPLE_HIG_AUDIT.md` (42 findings + 8 product-character findings, each carrying how it
was verified), `APPLE_DESIGN_SYSTEM.md` (thesis + full token contract with measured
contrast), `APPLE_POLISH_PLAN.md` (ranked ledger with honest open/done status).

**Defects found and fixed** (each reproduced in a real browser before being believed):
- Every `.notice` in the app rendered with **no border** — `--accent-dim` was referenced
  and never defined, which invalidates the whole `border` shorthand. Affected the
  storage-loss and resume-a-sit banners.
- Chart labels rendered at **4.44–4.93 px** on a 320 px phone.
- The five nav tabs did not fit at **any** phone width, with both scroll affordances
  suppressed, so Settings sat off-screen.
- The in-app guide made an unconditional privacy promise the app does not keep when the
  AI provider is on — **and a test pinned the false wording in place**.
- The post-sit review and AI draft destroyed keyboard focus and collapsed the section the
  user was working inside on every interaction.
- The orb never animated for a new user (settling countdown was off by default); the
  onboarding orb sat 38 px off-centre; its animation clobbered its own centring
  transform.
- A selected *recommended* preset showed no selected state.
- Learn's 17 collapsible sections showed no disclosure marker at all.

**Added:** a full light appearance (the app had none), increased-contrast and
reduced-transparency variants, a convertible tab bar (bottom on phones, top from 768px),
text equivalents for every chart, and semantic purpose-named colour tokens.

**Architecture unchanged:** one HTML file, no framework, no build step, no runtime
dependency, localStorage, offline via the service worker, **schema v6 untouched** — a
visual redesign that made zero data-contract changes. The ADR-0003 ceiling was **not**
moved: ~3,400 bytes were reclaimed from dead and duplicated code to fund the work.
Final payload **344,058 / 344,064 bytes** (6 free) — the binding constraint on what
remains open in `APPLE_POLISH_PLAN.md`.

**Verification:** Node **447/447** (plus new gates: whole-script syntax — the CORE
extraction previously let a syntax error anywhere in the app modules pass all 447 tests
while the app failed to boot — and duplicate `class` attributes), browser gates
**49/49**, interaction flow **35/35**, sweep at 320/360/375/390/430/768/834/1024 in both
appearances plus text at 150% and 200%, zero horizontal overflow and zero console errors.

**Independent review:** a fresh-context reviewer ran the app in a browser and returned
BLOCKED with five findings (frozen tab labels, keyboard-unreachable onboarding, a dead
Quiet-screen control, 200%-zoom overflow, clipped chart labels — three of the five caused
by this pass's own earlier fixes). All five were repaired, each repair gated; one repair
round introduced a further regression each (mid-word tab fracture; flattened line charts),
both caught by review, both fixed and gated. Final independent verdict on `78acb6a`:
**PASS**. Full trail in `APPLE_POLISH_PLAN.md`. Final payload **344,058 / 344,064**.
Real phone hardware remains untested.

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
  limitation).
- **Fresh-context adversarial review (2026-08-18, ~140k tokens, 35 tool calls):**
  2 BLOCKING + 6 NON-BLOCKING findings against a broad VERIFIED-PASS list
  (migration attacked live with a seeded v2 envelope; auto-save probed for
  duplicates/loss; certification greps; CORE purity re-proven; export hygiene;
  a11y sweep). Both blockers fixed with regression protection:
  (1) the orb settle animation was dead CSS — the static rule fired during
  prep too; fixed with `body.running:not(.settling)`, verified live
  (prep → orbBreathe, running → none/0.55), gate added to the test runner;
  (2) the Learn lights card attributed a visions instruction to Thai Forest
  that the ledger marks UNVERIFIED — attribution removed. Top non-blocking
  fixes: dull/pleasant/striving cards re-grounded to ledger-verified points
  (ledger expanded where the scout had verified more than the ledger recorded),
  "steadiest sits" question renamed "highest-contact sits" to match its metric,
  dead "source text" badge now applied to the Source library with an
  unaltered-companion-files note, MN 118 card source line now names the
  simile suttas. Accepted-as-recorded: byte headroom ~2 KB (ADR-0003 explains),
  CSV column order (header-driven, documented). After fixes: node suite
  447/447 + all runner gates; browser pass re-run 34/34; orb phase check PASS.

## Current practice position

- **Gate 0 — Foundation.** 30 minutes daily at the nostril rim / upper lip; count cycles
  1–8, restart; return without commentary; when the breath goes faint, wait.
- 30-day unbroken streak before booking the first retreat. Progress shows n/30 plus the
  descriptive "days sat, last 30".
- The owner's first real sit is imminent/logged — **treat any browser localStorage as
  production data.** Verification always happens on a throwaway localhost origin.

## App version & schema

- App **v4.5.0** (`CORE.APP_VERSION`), SW cache **v4.5.0** (`sw.js` SW_VERSION — ⚠ bump on
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
8. Mixed-version window (found by the 2026-09-08 review): after a deploy, an installed old
   client that opens the root URL before applying the update runs the new document under the
   old worker (the old cache stores it under `/`), while `start_url` still serves the old one.
   No data loss; records written in that window get stale `v` stamps and `undefined` v6 fields.
   Candidate fixes for a future version: per-record migration keyed on `v`, and/or precaching
   `./` (which would require a root rewrite on every host).

## Family distribution (no deploy)

Serve the folder on the home network (`python -m http.server 8080`), open
`http://<computer-ip>:8080/sit-tracker-v2.html` on each phone, follow Settings →
"Install on your phone", run the offline checklist, then testers use "Load demo data"
or their own sits and send feedback via the beta chip.

## Immediate next practice action

Sit 30 minutes today; press Start on the recommended card; log it honestly. After the
sit, tap the markers you actually used — the review timeline will pre-fill itself.
