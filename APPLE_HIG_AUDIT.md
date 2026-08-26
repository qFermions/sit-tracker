# Sit Tracker — HIG Audit (current state, v4.4.0)

Audited against the guideline corpus recorded in `APPLE_SKILL_PROVENANCE.md`, routed by
`APPLE_HIG_APPLICABILITY_MATRIX.md`.

**Method.** Five read-only scouts audited in parallel lanes (foundations, interaction,
product character, content screens, code/cleanup). Every finding below then went through
a verification step by the lead. The `Verified` column says how:

| Mark | Meaning |
|---|---|
| **browser** | Reproduced in headless Chromium against the running app. The number quoted is measured, not derived. |
| **computed** | Contrast ratios computed with the WCAG 2.1 relative-luminance formula from the app's own token values. |
| **code** | Read directly in the source and confirmed at the cited line. |
| **corrected** | A scout's claim that did not survive verification. Recorded with the correction, because a wrong finding acted on is worse than a missed one. |

Baseline at audit time: `sit-tracker-v2.html` = **341,984 bytes** against the
**344,064-byte** ceiling (ADR-0003) — **2,080 bytes** of headroom. Node suite
**447/447**. Branch `claude/practice-training-system` @ `a978767`, PR #2 open and draft.

---

## Severity summary

| Severity | Count |
|---|---|
| CRITICAL | 5 |
| HIGH | 14 |
| MEDIUM | 17 |
| LOW | 6 |

---

# CRITICAL

### C-1 · Every notice box in the app renders with no border — the token it references does not exist
**Screen:** all (storage-loss warning, update, backup reminder, resume-a-sit, demo, AI-engine, jhāna boundary, draft warnings)
**Verified:** **browser** — computed style on `.notice` returns `border-top-style: none`, `border-top-width: 0px`.

`.notice` declares `border:1px solid var(--accent-dim)`. **`--accent-dim` is never defined
anywhere in the 342 KB file.** Per CSS Custom Properties, a shorthand containing a `var()`
that is invalid at computed-value time is treated as `unset` for every longhand it
controls; `border-style` is not inherited, so it resolves to its initial value `none`.
`.notice.warn` overrides only `border-color`, which cannot resurrect a style of `none` —
so the *warning* variant is borderless too.

The two highest-stakes messages the app can show — "Local storage is unavailable… data
will be lost" and "A sit was in progress" — are among the affected.

> **Guideline — Layout > Best practices:** *"Group related items to help people find the
> information they want. For example, you might use negative space, background shapes,
> colors, materials, or separator lines to show when elements are related and to separate
> information into distinct areas."*

**Evidence:** `sit-tracker-v2.html:153` — `.notice{border:1px solid var(--accent-dim);…}`.
`:31` defines `--accent`, `--accent-deep`, `--accent-ink` — no `--accent-dim`.
**Fix:** point it at the token that exists (`--accent-deep`, 3.06:1 against the card — an
appropriate container edge). One token name. **Status:** open.

---

### C-2 · Chart axis and bar labels render at 4.4–4.9 px on a phone
**Screen:** Progress (all ten charts)
**Verified:** **browser** — measured chart box width per viewport, divided by the 600-unit `viewBox`:

| Viewport | Chart box | Scale | `font-size="10"` renders | `font-size="9"` renders |
|---|---|---|---|---|
| 320 px | 296 px | 0.493 | **4.93 px** | **4.44 px** |
| 360 px | 336 px | 0.560 | **5.60 px** | **5.04 px** |
| 390 px | 366 px | 0.610 | **6.10 px** | **5.49 px** |
| 430 px | 398 px | 0.663 | **6.63 px** | **5.97 px** |
| 768 px | 736 px | 1.227 | 12.27 px | 11.04 px |

The charts are legible only on a tablet. On every phone in the guideline's own device
table they are under half the stated minimum — and because SVG user units do not respond
to `rem`, they are also completely immune to the reader's text-size preference.

> **Guideline — Typography > Ensuring legibility:** *"Use font sizes that most people can
> read easily… Follow the recommended default and minimum text sizes for each platform."*
> Table: **Mobile — default 17 pt, minimum 11 pt.**
> **Guideline — Charting data:** *"you always want to make it easy for people to read a
> chart's details and descriptive text — like labels and annotations."*

**Evidence:** `:4159`, `:4186` (`font-size="10"`), `:4182` (`font-size="9"`); `:4149`
`const W = 600, H = 130`; `:126` `.chart svg{width:100%;height:auto}`.
**Fix:** move the sizing into CSS (`.chart text{font-size:19px}` in SVG user units) and
delete the three hard-coded attributes — net negative bytes, and it scales correctly at
every width. **Status:** open.

---

### C-3 · The in-app guide makes an unconditional privacy promise the app does not keep — and a test locks the false wording in place
**Screen:** Today → "how to use →"; invite text
**Verified:** **code** — `:1885`, `:2644`, `:1870`, compared against `:495`.

The guide states: *"Everything stays on this phone; nothing is uploaded anywhere."* That
is false whenever the optional AI provider is configured, at which point the user's
verbatim meditation journal is POSTed to a third-party endpoint. Settings gets it right
(`:495`: *"never leaves this device **unless you configure an AI provider** or export it
yourself"*) — so the app already knows the true sentence and prints the false one in the
surface most likely to be read.

Worse: `:2644` asserts the exact substrings `"stays on this phone"` and `"nothing is
uploaded"`, so correcting the copy trips a red test and reads like a regression. The
honesty architecture is this product's entire point; a test that pins a false claim is
the most serious defect in the audit even though nothing is visually wrong.

> **Guideline — Privacy:** *"Be transparent about how your app collects and uses people's
> data."*
> **Guideline — Generative AI:** *"Make sure people know if their information may be sent
> to a server, can see what's being shared, and understand what data may be stored
> off-device."*

**Fix:** make the guide and invite text carry the same conditional the Settings copy
already uses, and **invert the test** so it requires the qualifier instead of forbidding
it. Do not delete the locality promise — it is true and valuable; it just needs its one
real exception. **Status:** open.

---

### C-4 · The five navigation tabs do not fit at any phone width, and every scroll affordance is suppressed
**Screen:** all
**Verified:** **browser** — `nav.tabs` `scrollWidth` is **466 px** at every tested width, against `clientWidth` 286 / 326 / 356 px at 320 / 360 / 390 px viewports.

The bar is `width:fit-content` capped at `100% − 32px`, `overflow-x:auto`, with **both**
scroll indicators removed (`scrollbar-width:none` and `::-webkit-scrollbar{display:none}`).
At 390 px — a mainstream iPhone — **110 px is clipped**, and "Settings", which holds
export, backup, and the danger zone, sits off-screen behind an invisible boundary. There
is no fade, no partial-item peek, and no scrollbar.

> **Guideline — Layout > Visual hierarchy:** *"Take advantage of progressive disclosure to
> help people discover content that's currently hidden… you need to indicate that there
> are additional items that aren't currently visible."*

**Fix:** this is resolved structurally by the navigation rebuild (Design System, Part 7):
a bottom tab bar on compact widths that spans the full width, so five destinations fit
without scrolling at all. **Status:** open.

---

### C-5 · Post-sit review and AI draft destroy keyboard focus and collapse the section under the user on every interaction
**Screen:** Journal — review card, draft card
**Verified:** **code** — `:3594` (`box.innerHTML = …`), `:3812`, `:3801-3808`, `:3821`, `:4515`.

Both forms rebuild their entire card via `innerHTML` on every chip tap, radio change and
select change. Two consequences: focus falls to `<body>` after each interaction, and every
`<details>` is re-emitted without `open`, so the section the user is working inside snaps
shut. The worst case is self-defeating: `#rv-nim-cat` lives inside a `<details>`; choosing
"white light" collapses the very section that the choice was supposed to expand.

> **Guideline — Focus and selection:** *"People rely on the focus system to help them know
> where they are in your app. If you change focus without their interaction, people have to
> spend time finding the newly focused item, delaying their current task."*

**Fix:** record open state and the active element id before the rebuild; restore both
after wiring. ~200 bytes, fixes both halves. **Status:** open.

---

# HIGH

### H-1 · Tertiary text fails the contrast floor on three of the app's four surfaces
**Verified:** **computed.**

| `--fg-faint` `#76849b` on | Ratio | Verdict at `--fs-xs` (12.16 px) |
|---|---|---|
| `--bg` `#0a0e15` | 5.10:1 | pass |
| `--bg2` `#121926` | 4.65:1 | pass (thin) |
| card gradient top `#17202e` | **4.32:1** | **fail** |
| `--bg3` `#1a2333` | **4.16:1** | **fail** |
| recommended-preset top `#1d2331` | **4.15:1** | **fail** |

The token is paired with `--fs-xs` in nine separate rules and appears at 29 render sites.
`ARCHITECTURE.md:40` claims the ramp is *"all AA on their surfaces"*; measured, the
tertiary step is not.

> **Guideline — Accessibility > Vision:** *"Strive to meet color contrast minimum
> standards."* Table: **Up to 17 pt, all weights → 4.5:1.**

**Fix:** `--label-tertiary: #828fa5` — measured 4.82:1 on the worst surface, still visibly
a step below secondary. Byte-neutral. **Status:** open.

### H-2 · The app has no light appearance at all
**Verified:** **code** — `:6` `<meta name="color-scheme" content="dark">`; zero `prefers-color-scheme` rules in the file.
A person whose device is set to light gets a dark app with no say. The codebase is not
philosophically dark-only — `@media print` (`:247`) already renders light.
> **Guideline — Color > Best practices:** *"If you define a custom color, make sure to
> supply light and dark variants."*
**Fix:** the full verified light palette in the Design System, Part 3. **Status:** open.

### H-3 · No increased-contrast variant
**Verified:** **code** — zero `prefers-contrast` rules.
> **Guideline — Accessibility > Vision:** *"If your app doesn't provide this minimum
> contrast by default, ensure it at least provides a higher contrast color scheme when the
> system setting Increase Contrast is turned on."*
Given H-1, this is the escape hatch the guideline explicitly names, and it is absent.
**Status:** open.

### H-4 · Blurred surfaces with no reduced-transparency fallback
**Verified:** **code** — two `backdrop-filter` surfaces (`:146` dialog, `:151` toast), zero `prefers-reduced-transparency` rules. **Status:** open.

### H-5 · Onboarding overlay ignores safe areas and traps its own overflow above the fold
**Screen:** first run — the first screen anyone sees
**Verified:** **code** — `:228` `.onboard{position:fixed;inset:0;…display:flex;align-items:center;…overflow-y:auto}`.
Two compounding faults: no `env(safe-area-inset-*)` anywhere on a fixed full-screen
element (buttons under the home indicator, hero name under the notch), and the classic
centred-overflow trap — when content exceeds the container, `align-items:center` pushes
the overflow off the **top**, where scrolling cannot reach it. With a 130–180 px top
margin plus orb, title, copy and stacked buttons, that happens in landscape on phones in
the guideline's own device table, and in portrait at large text sizes.
> **Guideline — Layout > Guides and safe areas:** *"Safe areas are essential for avoiding a
> device's interactive and display features."* **Status:** open.

### H-6 · The onboarding orb is not where the layout reserves space for it
**Verified:** **browser** — computed `left` is **`16px`**, not `50%`; the orb's centre sits **38 px** left of its container's centre.
`.ob-orb` declares `left:50%;top:-40px` and then `inset:auto` **in the same block**.
`inset` is the shorthand for all four offsets, so the later declaration wipes the two
before it. Meanwhile `#ob-body{margin-top:130px}` dutifully reserves a large empty gap in
the centre for an orb that is no longer there.
**Fix:** move the reset ahead of the values it must not clobber — zero net bytes. **Status:** open.

### H-7 · The orb animation clobbers the centring transform it shares
**Verified:** **browser** — `@keyframes orbBreathe` animates `transform` (`transform: scale(.94)` / `scale(1.05)`), while `.ob-orb` uses `transform:translateX(-50%)` for centring.
While the animation runs, the animated value replaces the declared one entirely, so the
orb jumps sideways for its 24-second run and snaps back when it ends. Two visible lurches
bracketing the intro. Independent of H-6 — fixing H-6 alone leaves the lurch.
**Fix:** animate the independent `scale` property instead, leaving `transform` free. Net ~0 bytes. **Status:** open.

### H-8 · The settling countdown is off by default, so the app's only meaningful animation never runs for a new user
**Verified:** **browser** — `#opt-prep.checked === false`, and the attribute is absent.
The checkbox also lives inside a collapsed `<details>`. So for every new user `prepSec = 0`:
Start drops straight into a running sit, and the orb — whose entire documented purpose is
to *"settle WITH you during the countdown"* — never animates at all. The asymmetry is not
deliberate minimalism: `#opt-final` (Final bell) **is** checked by default.
> **Guideline — Settings:** *"Aim to provide default settings that give the best experience
> to the largest number of people."*
**Fix:** add `checked`. 8 bytes. Returning users are unaffected — `applySavedSitConfig`
re-derives the checkbox from stored `prepSec`. **Status:** open.

### H-9 · Nothing marks the transition from settling into the sit
**Verified:** **code** — `tick()` (`:3104`) rings only interval bells; `complete()` (`:3152`) rings the final bell; no prep→running edge detection; zero `navigator.vibrate` in the file.
The orb ceasing to breathe and the digits changing are the only signals that the sit has
begun — for a user who, by design, has their eyes closed.
> **Guideline — Motion:** *"Make motion optional… avoid using it as the only way to
> communicate important information… supplement visual feedback by also using alternatives
> like haptics and audio."* **Status:** open.

### H-10 · The disclosure triangle is absent from all 17 collapsible sections on Learn
**Verified:** **browser** — under `display:flex` the summary's text starts at the summary's own left edge (25 px = 25 px); switching the same element to `display:list-item` moves the text to 40 px, i.e. a 15 px marker box appears. The marker genuinely does not render.
`details summary{…display:flex;align-items:center}` (`:161`) overrides the default
`display:list-item`, which suppresses `::marker`. Learn carries 17 `<details>`, all closed
by default. Every one presents as a line of dim 14 px text with no indication it opens —
so the screen's entire navigation is invisible.
> **Guideline — Layout > Visual hierarchy:** *"…you might use a disclosure control…"*
**Fix:** restore `display:list-item` with padding instead of flex centring, keeping the
44 px target. **Status:** open.

### H-11 · Every history row hides its own content from screen readers
**Verified:** **code** — `:3930` `'<button class="sess-item" … aria-label="Open session ' + esc(s.date) + '">'`.
`aria-label` on a button overrides its entire subtree. Duration, contact minutes, ratio,
every badge, and the note excerpt — the whole editorial payload of the Journal list — are
unreachable. A screen-reader user hears only a date.
> **Guideline — Accessibility > Vision:** *"Describe your app's interface and content for
> screen readers."*
**Fix:** delete the `aria-label`; the visible children already name the button. Net −45 bytes. **Status:** open.

### H-12 · No chart has a text equivalent; every accessible name is a generic phrase with no values
**Verified:** **code** — `:4157`, `:4184` emit `role="img" aria-label="<o.label>"`, and the labels passed are `"ratio over time"`, `"duration vs contact"`, `"settling time"`, and six more. None contains a number, range, direction, or denominator.
Compounding it, the consistency calendar's per-day data lives in `<title>` children of
`<rect>`s inside a `role="img"` parent — which makes the graphic a leaf in the
accessibility tree, so those titles are never exposed, and they need hover, so they do not
exist on touch either.
> **Guideline — Charting data:** *"Make every chart in your app accessible… it's crucial to
> provide both accessibility labels that describe chart values and components."* **Status:** open.

### H-13 · Critical errors are delivered as a 3.5-second transient pill that cannot be re-read
**Verified:** **code** — `:2866` routes a localStorage write failure to `UI.toast(…)`; `:3339` auto-clears after 3,500 ms; `:151` `#toast{pointer-events:none;…z-index:50}`.
Silent data loss is announced the same way "Copied." is. A single shared timer means any
later toast clobbers it, and because an open `<dialog>` renders in the browser's top
layer, any toast fired while a modal is open is invisible regardless of z-index.
> **Guideline — Feedback:** *"Use alerts to deliver critical — and ideally actionable —
> information… you need to match the importance of the information to the level of
> interruption."*
**Fix:** route persistence failures to the existing persistent `#storage-warning` banner,
already in the DOM and styled. **Status:** open.

### H-14 · The Progress screen has no `h2`, and its 11 stat tiles silently mix all-time and range-scoped numbers
**Verified:** **code** — `:402-411` (no heading in the panel); `:4224-4236`.
The outline is `h1 → h3`. Six tiles read all-time metrics and five read range-scoped ones,
distinguished only by a 12 px note that never says *which* range. Tapping "7 d" leaves
"current streak", "days sat, last 30" and "longest streak" unchanged — which reads as a bug.
> **Guideline — Layout > Best practices:** *"Make essential information easy to find by
> giving it sufficient space."* **Status:** open.

---

# MEDIUM

### M-1 · Sub-44 pt touch targets
**Verified:** **browser**, rendered sizes swept across all five tabs:

| Control | Rendered | Note |
|---|---|---|
| `#tabbtn-today` … `#tabbtn-settings` (×5) | 77–102 **× 38** | primary navigation |
| `#guide-hint` | 103 **× 22** | *not reported by any scout — found in the lead's own sweep* |
| `#install-hint` | 144 **× 22** | *same* |
| `#bell-volume` | 200 **× 40** | |

> **Guideline — Accessibility > Mobility:** *"Offer sufficiently sized controls."* Table:
> **mobile default 44×44 pt, minimum 28×28 pt.** The two 22 px links are below the
> *absolute* minimum, not merely the default.

### M-2 · `#beta-chip` — **corrected**
A scout reported this as a 28 px target from its declared `min-height`. **Rendered size is
137 × 44** — padding and line-height carry it to the full target. **Not a defect.**
Recorded because the declared value is misleading and a future reader will re-flag it.

### M-3 · One radio label cancels the 44 pt rule inline
**Verified:** **code** — `:3556` `<label class="check" style="min-height:auto">`, defeating `.check{min-height:44px}`; with an 18 px radio the effective target is ~24 px, below the absolute minimum.

### M-4 · `--gold` carries six unrelated meanings
**Verified:** **code** — `:71` brand, `:115` timer phase, `:118` instruction accent, `:141` "traditional claim" epistemic label, `:158` current map stage, `:222-223` recommended preset.
A user who learns gold means *"traditional claim, treat sceptically"* then meets gold as
*"we recommend this."*
> **Guideline — Color > Best practices:** *"Avoid using the same color to mean different
> things."*
**Fix:** move *recommendation* onto `--accent`, leaving gold to mean only "traditional".

### M-5 · Two tokens named for appearance, one of them a duplicate meaning
**Verified:** **code** — `--teal` (`:55`) means "done" at `:181,182,190,191`, while `--ok` means the same thing at `:166,168`. `--indigo` (`:55`) is referenced once, inside a gradient, and never functions as a semantic colour.
> **Guideline — Color > System colors:** *"Each dynamic color is semantically defined by its
> purpose, rather than its appearance or color values."*

### M-6 · The dual-series chart's only legend names the two colours
**Verified:** **code** — `:4255` caption: `"blue = duration · gold = self-reported contact minutes"`; series fills `#4a7ba6` (`:4177`) and `#d4b078` (`:4178`), a blue/gold pairing the guideline names explicitly.
For a reader who cannot separate the two hues, a caption that says "blue" and "gold" is
not a fallback — it is the same information again.
> **Guideline — Accessibility > Vision:** *"…people who are color blind may have particular
> difficulty with pairings such as red-green and blue-orange. Offer visual indicators, like
> distinct shapes or icons, in addition to color."*

### M-7 · The consistency heatmap encodes everything in five shades with no legend and no non-colour channel
**Verified:** **code** — `:4201`; adjacent steps differ by 1.47–1.93:1, and the two lowest data steps measure 1.04:1 and 1.77:1 against the card. Thresholds (0 / <15 / <30 / <60 / ≥60) are stated nowhere.

### M-8 · The heatmap's rows are not weekdays, and a code comment claims an alignment the code never performs
**Verified:** **code** — `:4194` comment promises "find the sunday on/before"; `:4195-4199` computes `today − 111` with no weekday snapping and `row = i % 7`. Row 0 is whatever weekday fell 111 days ago, and it rotates on every new day. The GitHub-contribution form is borrowed and its contract broken.

### M-9 · Hindrance labels are truncated into nonsense
**Verified:** **code** — `:4270` takes `.split(" ")[0]`, then `:4182` applies `.slice(0,10)`. The five categories render as **"Sensual", "Ill", "Sloth", "Restlessne", "Doubt"**. The same slice turns `"afternoon (12)"` into `"afternoon "`, silently dropping the sample size.

### M-10 · All 14 modals share the accessible name "Dialog"
**Verified:** **code** — `:611` `<dialog id="modal" aria-label="Dialog">`, reused by 14 call sites (`:3355, 3976, 4008, 4087, 4534, 4608, 4632, 4757, 4828, 4927, 4953, 5022, 5056, 5213`). Each injects its own `<h2>`, but `aria-label` always wins.
> **Guideline — Modality:** *"Make it easy to identify a modal view's task."*

### M-11 · The danger-zone confirmation input has no label
**Verified:** **code** — `:4759` renders a bare `<input type="text" id="wipe-confirm">`; the instruction sits in an unassociated sibling `<p>`. A screen-reader user lands on an unnamed field guarding the app's only irreversible action.

### M-12 · Draft fields have no labels, and `null` is user-facing copy
**Verified:** **code** — `:4447` renders field names as `<span class="dim">`, never `<label for>`; `:4453` `placeholder="null"`; plus `<option value="">null</option>` ×3 and "will stay null" in prose. The review form already does this correctly with `placeholder="not reported"` (`:3648`).

### M-13 · The measure cap misses the two most important bodies of prose on Learn
**Verified:** **code** — `:138` caps `#tab-learn .card p,li,td`. The jhāna boundary sentence is a `.notice` (not a `p`), and the entire practice map renders into `#map-container`, a direct child of `#tab-learn` with no `.card` ancestor. Both run the full card width (~95ch) on desktop. **Fix is net −4 bytes.**

### M-14 · Journal's note excerpt is truncated twice, and the second truncation is invisible
**Verified:** **code** — `:3935` clips to 90 chars and appends its own "…"; `:136` then applies `white-space:nowrap` + `text-overflow:ellipsis`, showing ~35 characters at 320 px. The reader cannot tell which ellipsis they are seeing. It is also rendered in the weakest colour in the palette — this is the person's own writing, not metadata.

### M-15 · Search and filters give no scope, no result count, and no way out
**Verified:** **code** — `:390` `type="text"` (so no native clear); `:3937` shows a count only when results exceed 200; `:3919` filtered-empty state is a dead end with no reset control, while five selects can each hold a value.

### M-16 · The Progress empty state tells a returning practitioner they have never sat
**Verified:** **code** — `:4243` branches on the *selected range* being empty, not the store. A practitioner with 200 sessions who taps "7 d" after a week off is told *"Nothing here yet. That changes after one sit."* In an app whose stance is *"a missed day is data, not failure"*, that is both wrong and quietly shaming.

### M-17 · Source documents fetch with no loading state and no re-entrancy guard
**Verified:** **code** — `:5207` awaits `fetch()` with nothing shown until it resolves, and nothing disables the button. A second tap resolves into `showModal()` on an already-open dialog, which throws `InvalidStateError` *after* the body has been swapped — so the open dialog silently shows the wrong document.

---

# LOW

- **L-1 · `h1` and `h2` are the same size**, and an `h2` carrying `.section-title` renders at 12.16 px — *smaller than every `h3`* on the page, inverting the hierarchy. **code**, `:62`, `:63`, `:175`, `:334`.
- **L-2 · Six font weights, two of them non-canonical.** 650 and 750 resolve to 700 and 900 on the static fallback families (Roboto, Segoe UI), so the intended "one notch above bold" renders *heavier* than `h1`. **code**, `:60` + 10 sites.
- **L-3 · The timer numeral is `font-weight:300`** — a Light weight, on the most important number in the product. Largely self-mitigating at 54 px+, but the guideline names it explicitly. **code**, `:113`.
- **L-4 · `-webkit-text-size-adjust:100%`** suppresses the mechanism Chrome for Android uses to apply the OS text-scaling preference. Nothing requires it — `width=device-width` already prevents unwanted inflation. **code**, `:59`. *(Verified as a pass: the viewport meta sets no `maximum-scale` and no `user-scalable=no`, so pinch-zoom is intact.)*
- **L-5 · `100vh` / `85vh` resolve against the large viewport**, so a dialog can exceed the visible area while the URL bar is showing, pushing its confirm buttons below the fold. **code**, `:60`, `:146`.
- **L-6 · The toast has no bottom safe-area inset** — `bottom:24px` overlaps the home indicator, and in the installed PWA there is no browser chrome beneath to absorb it. **code**, `:151`.

---

# Product-character findings

These are judged against the product thesis rather than a HIG rule, and are labelled as
such rather than dressed in a fabricated citation.

### P-1 · HIGH · During a sit, "absence" is an opt-in the user must re-request every time
**Verified:** **code** — `:3443` hides only `#sit-config` while running; `#today-status` and `#practice-instructions` carry only `class="hide-zen"`; `:3455` calls `setZen(false)` on every non-running render, so the choice is never remembered.

Visible during a running sit, by default: the app header **including a "Private family
beta" feedback button**, the five-tab nav, update/backup/demo notices, the full
current-practice card, three stat tiles **including a streak counter**, three utility pills
**including "install on phone →"**, a redundant elapsed/planned line, a filling progress
arc, and **a full paragraph of practice instructions** — on screen while the eyes are
closed. Quiet screen is the only thing that produces absence, it is hidden until the sit
is already running, and it resets every time.

The reasoning that correctly demoted the orb in v4.4.0 was never applied to the twelve
other elements around it. **This is the highest-leverage change in the audit and it costs
no new UI.**

### P-2 · MEDIUM · The marker log reports on your attention to you, during the sit
**Verified:** **code** — `:330` `aria-live="polite"`; painted at `:3482`.
It prints your last four taps back at you (`steady @ 4′ · wandering @ 9′ · returned @ 9′`),
inviting exactly the commentary the app's own instruction forbids ("Return without
commentary"). For a VoiceOver user the interference is *louder*: the wandering count is
read aloud mid-sit.

### P-3 · MEDIUM · The streak cluster is the app's only real gamification, and it opens both home screens
**Verified:** **code** — Progress opens with three streak tiles (`:4225`, `:4227`), then a target line (`:4239` *"Gate 0 target… Current: N/30"*), then a 16-week contribution heatmap (`:4252`). Today's middle headline tile is a streak counter (`:4799`).
Each carries an honest caption — *"a missed day is data, not failure"* is a good sentence.
The finding is not that streaks exist; it is that they are three of the first three tiles
plus a target plus a chain graphic, which is a different thing.

### P-4 · MEDIUM · Uppercase micro-labels turn the record into instrumentation
**Verified:** **code** — four rules apply `text-transform:uppercase` (`:69`, `:122`, `:175`, `:188`, `:223`). Progress shows **eleven** simultaneously in a three-column grid; Today shows six. The source strings are already written in calm sentence case — the CSS is doing the shouting.

### P-5 · MEDIUM · AI provenance is captured, then discarded exactly where it matters
**Verified:** **code** — the draft screen handles attribution very well (names the engine, per-field confidence, quotes the evidence span, requires explicit confirmation). `aiConfidence` is persisted but never rendered again: session detail (`:3941`) never reads it, and the only surviving marker is a raw lowercase enum badge, `ai` (`:3927`). The **teacher report prints model-extracted numbers under the sentence "All values are the practitioner's own reports"** (`:4057`).

### P-6 · MEDIUM · Third-party retention is never mentioned
**Verified:** **code** — `:507` and `:4419` disclose *that* journal text is sent and *where* (naming the endpoint verbatim — genuinely better than most apps), but say nothing about retention, logging, or training by the receiving party.

### P-7 · LOW · A live percentage recalculates under the user's thumb moments after the bell
**Verified:** **code** — `:3623` renders `"concentration ratio: N%"` live as the contact-minutes slider moves. The thesis asks for *gentle reflection*; a score that updates as you drag converts an honest guess into a graded figure.

### P-8 · LOW · The practice map introduces gamification vocabulary in order to deny it
**Verified:** **code** — `:4354` *"A sober map, not a game. Levels do not unlock…"*. The user-visible level names never contain the word "level" and nothing auto-advances, so the denial is the only thing putting the frame in front of the reader.

---

# Verified as correct — do not regress

Recorded so a later pass does not "clean these up" and lose real value.

- **The already-saved contract is the strongest interaction design in the file.**
  `TIMER.complete()` writes the session *before* opening the review (`:3176`); the dismiss
  control reads **"Close — sit is saved"** (`:3606`); the copy says *"Close anytime;
  nothing is lost"* (`:3608`). The review is an inline card, not a modal — correct, since
  a 15-field enrichment form is exactly the wrong thing to trap someone in.
- **Timer live-region hygiene is right:** `#timer-display` is `role="timer" aria-live="off"`
  so per-second updates are not announced, while `#timer-phase` (polite) carries state
  changes and `#timer-live` carries start/pause/resume/complete.
- **Reduced-motion coverage is complete.** `*{animation:none!important;transition:none!important}`
  (`:170`) catches every animation and transition in the file. *(The duplicate rule at
  `:244` is redundant — `!important` already won — and is 57 free bytes.)*
- **Destructive actions are confirmed proportionally**, and the full wipe requires typing
  `DELETE` with the confirm button disabled until it matches. Import shows a preview with
  new/duplicate/invalid counts before writing.
- **Native `<dialog>` + `showModal()`** gives Escape-dismiss, backdrop, focus containment
  and focus restoration for free across all 14 modals.
- **Export hygiene:** the AI key is stripped from JSON exports (`:4585`); demo and test
  entries never reach statistics, exports, share cards, or the teacher report.
- **Honest denominators throughout.** Observations count only *answered* questions and say
  so; `notEnough()` states the exact shortfall. Every observation carries range, n, metric
  and evidence strength.
- **The boundary rule holds.** Nothing in the app infers a meditative state; `MAP_EVIDENCE`
  is never auto-set; the jhāna boundary sentence is test-guarded.
- **Zero cheerleading.** No exclamation marks in user-facing strings, no "Great job", no
  "Keep it up". Empty states carry personality without hype.
- **The four traditions' content is the best part of the app** — disagreements shown
  per-teacher rather than averaged, unverified attributions removed rather than softened.
  The finding at M-13 and the presentation notes are layout only; **the doctrinal text is
  not to be touched.**
- **Colour-only signalling, checked and cleared:** `.conf-high/medium/low` render their
  word inside the coloured span; `.diff-old` carries `line-through`; `.tstat.done` reads
  "recorded ✓". These are *reinforcement*, not colour-only, and must not be "fixed".
- **`.today-done` is a dead rule** — the class is never emitted by any code path.
- **Measure discipline** (`main{max-width:860px}` plus a 64ch cap) is sound where it applies.
- **Audio unlock is handled on the user gesture**, the only reliable place.
- **Interrupted-sit recovery is a non-modal inline banner**, and onboarding is correctly
  suppressed while recovery is pending.
