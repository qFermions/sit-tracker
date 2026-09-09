# Sit Tracker — Design System

Grounded in the guideline corpus recorded in `APPLE_SKILL_PROVENANCE.md` and routed by
`APPLE_HIG_APPLICABILITY_MATRIX.md`. Every contrast figure in this document was
computed with the WCAG 2.1 relative-luminance formula against the app's own surface
values — none are estimated.

---

# Part 0 — Night Practice + Apple restraint (v4.6.0, 2026-09-09)

The v4.6.0 pass keeps the thesis and the semantic token layer below and re-picks the
values and the surfaces. It is HIG-inspired, not an Apple certification; the skill's
pinned corpus (`APPLE_SKILL_PROVENANCE.md`) was reused as reference, and the official
Materials / Accessibility / Typography / Motion pages were the primary external reference.

**Direction.** Dark is the home appearance: a near-black ground, gently separated charcoal
surfaces, warm labels, one restrained amber emphasis. Light is a warm paper ground with ink
text and a contrast-safe brown-amber accent, calibrated on its own, never inverted.

**What changed visibly.** The sit leads: orb, time and one dominant Start action are the
first thing on Today at every width; the remembered practice, its configuration and one
continuity line follow, then the presets. Statistics tiles, the "works offline" pill and
the header beta chip are gone from Today (feedback stays in Settings; how-to-use and
install remain as quiet links). The timer stage sits on the open ground, not in a box.
Cards are flat surfaces with a single edge — no gradients, glows or drop shadows; Journal
history is a list; Learn is an editorial page; Settings groups carry small capital headers.
The tab bar is translucent over content with an opaque fallback under reduced
transparency; the active tab is a soft amber tint. Markers no longer fracture mid-word.

**Tokens (dark → light).** background `#0b0b0d` → `#f7f4ee` · surface `#151517` → `#fffdf9`
· surface-elevated `#1f1f23` → `#efeae1` · separator `#28282d` → `#e2ddd3` · label-primary
`#f2ede4` → `#1c1913` · label-secondary `#b2aa9d` → `#585247` · label-tertiary `#8e877b` →
`#6a635a` · accent `#e2a75c` → `#9a5b0f` (on-accent `#1b1205` → `#fff`) · tradition
`#d6b47c` → `#7a5a1f` · destructive `#ee9188` → `#a52c2c` · glass `rgba(17,17,19,.82)` →
`rgba(255,253,249,.86)` · tint = accent at 12 %. Radii 22/14/10 px; spacing 4·8·12·16·24·40;
motion 120/220/480 ms with one ease-out; the only ambient loop is the optional settling orb.
Type: system stack with Burmese fallbacks (`"Noto Sans Myanmar","Myanmar Text"`); body
17 px (`--fs-md: 1.0625rem`), secondary 15 px, captions 13 px; the timer stays Regular (400,
per Part 2 — never Light), tabular, `clamp(2.2rem, 14vw, 5.25rem)` and never wraps (a 1 h+
reading fits 320 px). The wordmark keeps `overflow-wrap: normal` so 200 % text cannot fracture
it. During a sit and on the Quiet Screen the header is hidden, so `main` carries the top safe-area
inset itself. `theme-color` follows the ground in both appearances.

**Measured contrast (WCAG 2.1 relative luminance, computed 2026-09-09; the browser gates
re-measure rendered text in both appearances):** dark, on the background — label-primary
16.9:1, label-secondary 8.5:1, label-tertiary 5.5:1, accent 9.3:1, tradition 10.0:1,
destructive 8.5:1; on a surface — secondary 7.9:1, tertiary 5.1:1; on-accent text on the
accent 8.7:1. Light, on the paper ground — label-primary 16.0:1, label-secondary 7.1:1,
label-tertiary 5.4:1, accent 4.9:1, tradition 5.8:1, destructive 6.4:1; on a surface —
secondary 7.6:1, tertiary 5.8:1; white on the accent 5.4:1. Increased-contrast variants
lift the secondary and tertiary labels and the separators in both appearances.

**Budget.** The redesign reclaimed bytes: 344,058 → 339,746 (ADR-0003 ceiling 344,064,
headroom 6 → 4,318) by consolidating the stylesheet (23.3 KB → 20.4 KB), removing the
gradient/elevation layer and the Today tile renderer.

---

# Part 1 — The thesis

> **Opening Sit Tracker should feel like approaching a meditation cushion.**

That single sentence decides every argument in this document. A cushion does not greet
you. It does not report your weekly total. It is simply there, in the same place,
ready. The whole design goal is to build software with that quality of presence.

Four movements follow from it:

| Moment | What the interface owes you | What that means concretely |
|---|---|---|
| **Before a sit** | **Clarity** | One screen answers three questions and nothing else: *what am I practising, for how long, how do I begin.* |
| **During a sit** | **Absence** | The UI is interference. Every pixel still on screen must justify why it did not get out of the way. |
| **After a sit** | **Gentle reflection** | The sit is already saved. Reflection is an offer, never a toll gate. |
| **Later** | **Useful memory** | A private record you can actually search and re-read — not a performance review. |

## What this product is not

These are hard constraints, not preferences:

- **No dashboard energy.** Statistics are not the product. Practice is.
- **No SaaS energy.** No onboarding funnels, no empty-state marketing, no upsell.
- **No wellness-marketing energy.** No "your mindfulness journey."
- **No gamification.** No badges, no points, no rewards, no nudges to keep a run alive.
- **No attainment meters.** The app records what you report. It never grades it.
  *"The app records your practice. It does not decide what meditative state you
  attained."*
- **No decorative gradients.** A gradient must do work or it goes.
- **No card soup.** Eleven equal-weight cards in a row is not organisation.
- **No lotus clichés, no glowing enlightenment graphics.**

## And what it is not allowed to become

Separately, and equally binding: this redesign **does not imitate Apple**. No Apple
branding, no fake device chrome, no Apple assets, no bundled proprietary Apple fonts,
no repackaged Apple symbol set, and no glass-everywhere pastiche. The guidelines
inform *how the app treats its user*. The app keeps its own face — midnight ground,
one moonlit accent, Burmese ဈာန် in the wordmark, and the orb.

---

# Part 2 — Type

## Faces

One stack, zero embedded bytes:

```css
--font-system: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
```

No SF Pro files, no webfont, no `@font-face`. Typography guidance is explicit that you
should *"Access all system fonts — don't embed system fonts in your app or game"*
(`typography.md`), and a downloaded font would break the zero-dependency architecture
anyway.

Numerals are tabular everywhere a number can change in place — the timer, durations,
counts, chart labels — so digits do not jitter:
`font-variant-numeric: tabular-nums`.

## Weights — a correction to the current app

`typography.md` is unambiguous:

> *"In general, avoid light font weights. For example, if you're using system-provided
> fonts, prefer Regular, Medium, Semibold, or Bold font weights, and avoid Ultralight,
> Thin, and Light font weights, which can be difficult to see, especially when text is
> small."*

The app previously set the timer in `font-weight:300` — a Light weight, at the single
most important number in the product. It also used six weights (300/600/650/700/750/800),
several of which do not render distinctly in a system-font stack that lacks the matching
variable axis; on the static fallback families (Roboto, Segoe UI) 650 rounds to 700 and
750 rounds to 900, so the intended "one notch above bold" rendered *heavier* than `h1`.
All six are now collapsed to the four below. The timer is **Regular 400**, not Bold:
Regular satisfies the guideline and is the calmer choice for a meditation clock.

**The system is four weights and no more:**

| Role | Weight | Used for |
|---|---|---|
| Regular | 400 | Body text, long-form reading, **the timer** |
| Medium | 500 | Secondary labels, metadata |
| Semibold | 600 | Buttons, section titles, list emphasis |
| Bold | 700 | Screen titles and headline numbers |

## Scale — semantic roles, not t-shirt sizes

The current scale (`--fs-hero`, `--fs-xl`, `--fs-lg`, `--fs-md`, `--fs-sm`, `--fs-xs`)
names sizes. Sizes cannot tell you where they belong, so they get used arbitrarily.
The replacement names *roles*, the way system text styles do:

> **Implementation note.** The *roles, sizes and weights* below shipped as specified.
> The token **names** were left as the existing `--fs-*` identifiers rather than renamed
> to `--text-*`: the rename is purely cosmetic in the source, and at the time it was
> considered the payload had 101 bytes of headroom. Recorded as a deliberate trade, not
> an omission — the mapping is one-to-one and given in the last column.

| Token (shipped) | Size | Weight | Role |
|---|---|---|---|
| `--fs-timer` | `clamp(2.2rem, 15vw, 6rem)` | 400 | The running clock. One instance in the app. |
| `--fs-hero` | `clamp(2.4rem, 8vw, 3.6rem)` | 700 | First-open wordmark only. |
| `--fs-display` | `clamp(1.8rem, 5.5vw, 2.6rem)` | 700 | Stat and tile headline numbers. |
| `--fs-xl` | `1.5rem` | 700 | `h1` — the app title. |
| `--fs-lg` | `1.18rem` | 700 | `h2` — card headings. |
| `--fs-md` | `1rem` | 600 / 400 | `h3` at 600; reading text at 400. **Default body size.** |
| `--fs-sm` | `0.875rem` (14 px) | 400 | Secondary prose, form labels, metadata. |
| `--fs-xs` | `0.8125rem` (13 px) | 500 | The smallest text in the app. |

**Two rules govern the small end.** `typography.md` gives mobile a **17 pt default and
an 11 pt minimum**. `--fs-md` at `1rem` = 16 px sits at the default; `--fs-xs`
was raised from `.76rem` (≈ 12.2 px) to `0.8125rem` = 13 px. The old value was legal but
was being asked to carry real information at the weakest colour in the palette, which
failed contrast on three of four surfaces — see Part 3.

**Text zoom must work.** Every size is expressed in `rem`, so browser text-size settings
and page zoom scale the whole interface. The three `clamp()` values are deliberate
exceptions on display type only; their **floors are in `rem`**, so they still scale with
the reader's text size, and their `vw` middle term lets them grow with the viewport.
The timer's floor is `2.2rem` rather than `3.4rem` for a measured reason: at 200% text on
a 320 px screen a `3.4rem` floor is 108.8 px and pushes the page sideways. Verified: no
horizontal overflow at 320 px and 390 px, at both 150% and 200%, and machine-gated. Guidance asks that layouts *"adapt to all font
sizes"* and that we *"Keep text truncation to a minimum as font size increases"*
(`typography.md`) — the truncation audit is in the polish plan.

**Tab titles do not scale with body text.** `typography.md`: *"when people increase text
size in a tabbed interface, they don't expect the tab titles to increase in size."*

## Measure

Reading text is capped at `68ch`. The current app applies a `64ch` cap to `#tab-learn`
only; prose exists on other screens too and is currently unbounded on wide displays.

---

# Part 3 — Colour

## The principle

`color.md`: *"Each dynamic color is semantically defined by its purpose, rather than
its appearance or color values."* And: *"Avoid redefining the semantic meanings of
dynamic system colors... don't use the separator color as a text color, or secondary
text label color as a background color."*

The current tokens are named for appearance (`--bg2`, `--fg-dim`, `--line-hi`). A token
called `--bg2` cannot tell you whether it is the right background for a grouped card or
a modal, so the choice gets made by eye each time and drifts. The replacements are named
for purpose.

## The token set

**Backgrounds** — three levels of hierarchy, per `color.md`'s *"Primary for the overall
view / Secondary for grouping content or elements within the overall view / Tertiary for
grouping content or elements within secondary elements."*

| Token | Purpose |
|---|---|
| `--background` | The page ground. |
| `--surface` | A card or grouped region on the ground. |
| `--surface-elevated` | Content grouped *inside* a surface; also the raised control fill. |

**Labels** — four descending levels, mirroring the Label / Secondary / Tertiary /
Quaternary roles `color.md` defines for foreground content.

| Token | Purpose |
|---|---|
| `--label-primary` | Primary content. |
| `--label-secondary` | Supporting content. |
| `--label-tertiary` | Metadata, captions, timestamps. |
| `--placeholder` | Placeholder text only. Never a label. |

**Structure and meaning**

| Token | Purpose |
|---|---|
| `--separator` | Hairlines between rows and sections. **Never text.** |
| `--separator-strong` | The one heavier divider, for control borders. |
| `--accent` | Interactivity. Exactly one meaning: *you can act on this.* |
| `--on-accent` | Text/glyph colour on an accent fill. |
| `--tradition` | The gold used to mark a traditional claim. Not a warning. Not a highlight. |
| `--success` `--warning` `--destructive` | State. Always paired with a word or shape. |

`color.md`: *"Avoid using the same color to mean different things."* The gold is the
live risk here — today it marks traditional claims (`.badge.gold`), the timer phase
line, and the recommended preset. Those are three different meanings on one colour. The
polish plan resolves it.

## Values, with measured contrast

Every ratio below is computed, worst-case, against the **least favourable surface the
token can legally appear on**.

### Dark (the app's home appearance)

| Token | Value | Worst-case contrast | Against |
|---|---|---|---|
| `--background` | `#0a0e15` | — | — |
| `--surface` | `#121926` | — | — |
| `--surface-elevated` | `#1a2333` | — | — |
| `--label-primary` | `#e9eef6` | **13.53:1** | `#1a2333` |
| `--label-secondary` | `#9fadc0` | **6.92:1** | `#1a2333` |
| `--label-tertiary` | `#828fa5` | **4.82:1** | `#1a2333` |
| `--accent` | `#8ec3ea` | **8.37:1** | `#1a2333` |
| `--on-accent` | `#0a1520` | **9.77:1** | on `#8ec3ea` |
| `--tradition` | `#d4b078` | **7.72:1** | `#1a2333` |
| `--success` | `#86c996` | **8.11:1** | `#1a2333` |
| `--warning` | `#ddb076` | **7.92:1** | `#1a2333` |
| `--destructive` | `#e08b8b` | **6.18:1** | `#1a2333` |
| `--separator` | `#253044` | 1.19:1 — non-text, decorative only | `#1a2333` |

> **The one change to the dark palette.** `--label-tertiary` moves from the old
> `--fg-faint #76849b` to **`#828fa5`**. Measured: `#76849b` scores **4.16:1** on
> `--surface-elevated` and **4.32:1** on the card-gradient top stop `#17202e` — both
> below the 4.5:1 floor that `accessibility.md` sets for text up to 17 pt, and this
> token carries the smallest text in the app. `#828fa5` clears it at 4.82:1 while
> staying visibly recessive. Every other dark value already passed and is kept —
> the existing palette was measured before it was changed.

### Light (new — the app currently has none)

`color.md`: *"If you define a custom color, make sure to supply light and dark
variants."* The app today ships `<meta name="color-scheme" content="dark">` and zero
`prefers-color-scheme` rules, so a person whose device is set to light gets a dark app
with no say in it.

| Token | Value | Worst-case contrast | Against |
|---|---|---|---|
| `--background` | `#f5f6f8` | — | — |
| `--surface` | `#ffffff` | — | — |
| `--surface-elevated` | `#eef1f5` | — | — |
| `--label-primary` | `#11151c` | **16.15:1** | `#eef1f5` |
| `--label-secondary` | `#515c6b` | **5.99:1** | `#eef1f5` |
| `--label-tertiary` | `#616b7a` | **4.76:1** | `#eef1f5` |
| `--accent` | `#1f6191` | **5.83:1** | `#eef1f5` |
| `--on-accent` | `#ffffff` | **6.61:1** | on `#1f6191` |
| `--tradition` | `#7a5a1f` | **5.60:1** | `#eef1f5` |
| `--success` | `#1f6b42` | **5.72:1** | `#eef1f5` |
| `--warning` | `#8a5a12` | **5.22:1** | `#eef1f5` |
| `--destructive` | `#a52c2c` | **6.19:1** | `#eef1f5` |
| `--separator` | `#d9dee6` | 1.19:1 — non-text, decorative only | `#eef1f5` |

Light is not a tint of dark. The accent had to be re-picked entirely: `#8ec3ea` scores
about 1.7:1 on white and is unusable as a light-mode accent. Light mode is a paper
ground, not a white one — `#f5f6f8` under white cards keeps the calm and avoids glare.

## Never colour alone

`accessibility.md`: *"Convey information with more than color alone... Offer visual
indicators, like distinct shapes or icons, in addition to color to help people perceive
differences in function and changes in state."*

Every state in this app pairs colour with a **word or a shape**:

- Confidence levels (`.conf-high/medium/low`) carry their word, not just their hue.
- Diff markers keep `line-through` on the old value as well as the red.
- A completed-today indicator keeps its text label alongside the teal.
- The "Danger zone" heading is identified by its **words**, not by being red.
- Badges are distinguished by their **text**; gold is reinforcement, never the signal.

## Appearance switching

Three states, and the page must be correct in all of them:

1. `prefers-color-scheme: dark` → dark tokens.
2. `prefers-color-scheme: light` → light tokens.
3. There is deliberately **no in-app theme switch.** The app follows the device, which is
   what the setting is for; a third control would add Settings surface and bytes for a
   preference the OS already owns. Recorded as a decision, not an oversight.

`<meta name="color-scheme" content="dark light">` so form controls, scrollbars, and the
caret adopt the right appearance. Tokens are defined once on `:root` and *redefined*
per appearance — never defined only inside a media query.

---

# Part 4 — Space

An 8-point rhythm with one 4 pt half-step:

| Token | Value |
|---|---|
| `--sp-1` | 4 px |
| `--sp-2` | 8 px |
| `--sp-3` | 12 px |
| `--sp-4` | 16 px |
| `--sp-5` | 24 px |
| `--sp-6` | 40 px |

Retained from the existing app — it was already coherent, and churn here would cost
bytes for no user-visible gain.

**Control spacing is a size requirement, not a polish item.** `accessibility.md`:
*"Consider spacing between controls as important as size."* Adjacent controls get at
least `--sp-2` between them; unrelated controls get `--sp-4` or a separator.

**Safe areas.** `layout.md` calls safe areas *"essential for avoiding a device's
interactive and display features."* Every edge-anchored element must respect them —
including the toast and any bottom navigation, which the current app's fixed
`bottom:24px` toast does not.

---

# Part 5 — Shape, depth, and material

## Corners

| Token | Radius | Applied to |
|---|---|---|
| `--r-sm` | 10 px | Inputs, chips, small controls |
| `--r` | 14 px | Cards, buttons |
| `--r-lg` | 22 px | Sheets, dialogs, the timer card |
| `--r-pill` | 999 px | Pills and segmented controls only |

A larger container never has a smaller radius than the thing nested inside it.

## Elevation

Three levels, and they mean altitude — not decoration:

- `--elev-1` — a card resting on the ground.
- `--elev-2` — something temporarily above the page (toast, active sheet).
- `--elev-3` — a modal dialog, the only thing that blocks the app.

## Material, used sparingly

Glass appears in exactly **two** places: the modal dialog and the toast. Both are
transient, both float over content, and both are cases where seeing the layer beneath
communicates *"this is temporary; your page is still there."* Nothing else gets a
backdrop filter. This is a deliberate reading of the owner's constraint — *do not turn
everything into glass* — and of `materials.md`'s restraint.

**Translucency must be optional.** Where a `backdrop-filter` is used, a
`prefers-reduced-transparency: reduce` rule must replace it with an opaque fill. The
app currently has two blurred surfaces and **zero** reduced-transparency handling.

## Gradients

Three recipes, each with a job:

- **Page wash** — a very slight radial lift at the top of the ground, so the page has a
  horizon rather than a flat field.
- **Card sheen** — a two-stop vertical that separates a card from the ground without a
  heavy border.
- **Primary action** — the one call to action.

Any gradient that cannot name its job is deleted.

---

# Part 6 — Motion

`motion.md` governs, and the product adds a stricter rule of its own.

- **Vocabulary:** `--dur-1` 120 ms (press feedback), `--dur-2` 220 ms (transitions),
  `--dur-3` 480 ms (entrances). Easing `cubic-bezier(.16, 1, .3, 1)`.
- **Only `transform` and `opacity` animate.** No layout-triggering animation.
- **Nothing loops while idle.**
- **Every animation must communicate something.** Motion that only decorates is removed.

**The orb rule — a product contract, not a style choice.**

> The orb breathes *with you* during the settling countdown, then **holds completely
> still for the sit itself**, because the object of the practice is the breath at the
> nostrils, not the screen.

This is enforced by a regression gate in `tests/run-core-tests.mjs` and must survive the
redesign untouched.

**Reduced motion.** `accessibility.md` asks that when Reduce Motion is on, apps *"respond
by reducing automatic and repetitive animations"* and suggests *"Replacing transitions
in x-, y-, and z-axes with fades to avoid motion."* All looping and translating
animation stops; opacity fades may remain.

---

# Part 7 — Navigation

Five destinations, flat, always visible: **Today · Journal · Progress · Learn ·
Settings**. No hamburger, no nesting, no hidden sixth thing.

`layout.md` offers the resolution to the mobile/desktop tension directly:

> *"Consider a convertible tab bar for adaptive navigation. For many apps, you don't
> need to choose between a tab bar or sidebar for navigation; instead, you can adopt a
> style of tab bar that provides both... As the view resizes, the presentation style
> changes to fit the width of the view."*

So:

| Width | Presentation |
|---|---|
| Compact (phone) | Bottom tab bar, thumb-reachable, above the home-indicator inset |
| Regular (tablet / desktop) | Top-anchored — because `layout.md` also warns, for desktop, to *"Avoid placing controls or critical information at the bottom of a window."* |

**Requirements in both presentations:** every destination is a ≥44×44 pt target; the
current label is identifiable without colour; the bar respects
`env(safe-area-inset-bottom)`; and the tablist is operable by keyboard.

---

# Part 8 — Controls

| Control | Minimum | Note |
|---|---|---|
| Any tap target | **44 × 44 pt** | `accessibility.md`: mobile default control size 44×44 pt. |
| Buttons | 44 pt tall | Primary actions 56 pt. |
| Checkbox / radio | 18 px visually, **44 pt hit area** | The visual box may stay small; the *target* may not. |
| Range slider | 44 pt tall | Currently 40 px. |
| Tab bar item | 44 pt | Currently 38 px. |
| Chips / small pills | 44 pt | Currently one at 28 px. |

Focus is always visible: `:focus-visible` gets a 2 px `--accent` outline at 2 px offset,
on every interactive element — including any control that is visually hidden but still
reachable by keyboard.

**No hover-only affordances.** `pointing-devices.md` applies to the desktop case, but the
binding rule is simpler: if information or an action is revealed only on `:hover`, it
does not exist for touch or keyboard users.

---

# Part 9 — What this system must not cost

This redesign is **not** permission to abandon the small-app architecture. All of the
following survive unchanged:

- One HTML file. No framework, no build step, no runtime dependency, no package manager.
- `localStorage` persistence, current schema, backward compatible.
- Offline-first via the service worker.
- The payload ceiling of **344,064 bytes**, machine-enforced (ADR-0003).

A visual redesign should make **zero** data-contract changes.

Bytes for new work are funded by **removing obsolete and duplicated CSS first**, not by
raising the ceiling. Measured cost of the semantic token rename alone was **+831 bytes**
against **2,080 bytes** of starting headroom — which is why the reclamation pass came
first rather than last. It reclaimed roughly **3,400 bytes** (dead rules and tokens,
duplicate selectors, a shared card-surface rule, merged stat/tile inner elements,
utility classes for repeated inline styles, a shared field-wrapper fragment, and 23 CORE
export names never referenced anywhere). **The ceiling was not moved.** Final payload:
**343,963 of 344,064 bytes.**

`sw.js`'s `SW_VERSION` must move with every HTML payload change. No exceptions: an
installed client that does not see a new cache version never receives the redesign.
