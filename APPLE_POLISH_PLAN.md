# Apple Polish Plan — ranked ledger

Derived from `APPLE_HIG_AUDIT.md`. Ranked P0 (ship-blocking) to P4 (nice to have).
Status is factual: **DONE** means implemented *and* verified by a named check.

Payload reality throughout: the app must stay under **344,064 bytes** (ADR-0003). It
started this pass at 341,984 with 2,080 bytes of headroom and ends at **344,058 with
6 bytes free**. Roughly **3,700 bytes** were reclaimed from dead and duplicated code, and
a further **312** from removing a redundant onboarding step, to fund the work.
**The ceiling was not moved.** That constraint is the honest reason several P2–P4 items
below are still open, and it is called out per item.

---

## P0 — ship-blocking

| # | Item | Status | Verified by |
|---|---|---|---|
| P0-1 | `.notice` rendered with **no border anywhere** — `--accent-dim` was used and never defined, invalidating the whole shorthand | **DONE** | Browser: `border-top-style` was `none`, now `solid 1px` in both appearances |
| P0-2 | Chart labels rendered at **4.44–4.93 px** on a 320 px phone | **DONE** | Sized in CSS user units; measured chart box ÷ viewBox at nine widths |
| P0-3 | The in-app guide made an unconditional "nothing is uploaded" promise the app does not keep, and **a test pinned the false wording** | **DONE** | Copy corrected in guide + invite; test inverted to require the qualifier; 447/447 |
| P0-4 | Five nav tabs did not fit at any phone width, with both scroll affordances suppressed | **DONE** | `scrollWidth` was 466 vs 356 client at 390 px; now fits at 320–1024, gated |
| P0-5 | Post-sit review and AI draft destroyed keyboard focus and collapsed the open section on every interaction | **DONE** | Interaction flow: section stays open, focus not on `<body>`, light-category case explicitly covered |

## P1 — accessibility release gate

| # | Item | Status | Verified by |
|---|---|---|---|
| P1-1 | Tertiary text failed 4.5:1 on three of four surfaces | **DONE** | `#76849b` → `#828fa5`; worst case 4.16:1 → 4.82:1, computed |
| P1-2 | No light appearance at all | **DONE** | Full palette, every value re-picked and verified; renders at eight widths |
| P1-3 | No increased-contrast variant | **DONE** | `prefers-contrast: more` for both appearances |
| P1-4 | Two blurred surfaces, no reduced-transparency fallback | **DONE** | `prefers-reduced-transparency: reduce` |
| P1-5 | Charts had no text equivalent — generic names, no values | **DONE** | Line/bar announce count, range, max; calendar announces days sat |
| P1-6 | Chart colours were hardcoded and ignored the appearance (axis text 3.4:1 on a white card) | **DONE** | Moved to CSS; zero hardcoded SVG colours remain |
| P1-7 | Sub-44 pt targets: 5 nav tabs (38), two links (22), range (40), beta chip (28, latent) | **DONE** | Rendered-size sweep across all five tabs: 0 remaining |
| P1-8 | Every history row hid its own content from screen readers via `aria-label` | **DONE** | Override removed; net −45 bytes |
| P1-9 | All 14 modals shared the accessible name "Dialog" | **DONE** | Named from each modal's own heading; gate opens a real modal and reads it |
| P1-10 | The delete-everything confirmation input had no accessible name | **DONE** | `<label for>` + placeholder |
| P1-11 | Text zoom overflowed horizontally at 150% and 200% | **DONE** | Header wrap + timer clamp floor; gated at 320/390 px × 150/200% |
| P1-12 | Learn's 17 collapsible sections showed no disclosure marker | **DONE** | `display:list-item` restored; marker box measured at 15 px |
| P1-13 | The tablist is not operable with arrow keys | **OPEN** | Blocked on payload (~180 bytes). The tabs are reachable and operable by Tab + Enter today, so this is a convention gap, not an access gap |

## P2 — platform conventions and correctness

| # | Item | Status | Notes |
|---|---|---|---|
| P2-1 | The orb never animated for a new user — the settling countdown was off by default | **DONE** | `checked` added; interaction flow asserts it |
| P2-2 | `.ob-orb` sat 38 px off-centre — a later `inset:auto` wiped `left`/`top` | **DONE** | Declaration order fixed; computed `left` was `16px`, now `50%` |
| P2-3 | `orbBreathe` animated `transform`, clobbering the centring `translateX` | **DONE** | Animates the independent `scale` property; orb now settles rather than snaps |
| P2-4 | A selected *recommended* preset showed no selected state (equal specificity, later rule won) | **DONE** | Compound selector; verified by forcing both states and diffing |
| P2-5 | Toast and tab bar ignored the bottom safe area | **DONE** | `env(safe-area-inset-bottom)` on both |
| P2-6 | `100vh` / `85vh` could push a dialog's buttons below the fold | **DONE** | `dvh` |
| P2-7 | Six font weights, two non-canonical (650→700, 750→900 on static fallbacks) | **DONE** | Four weights only |
| P2-8 | Nothing marks the settling→sit transition for someone with their eyes closed | **OPEN** | ~150 bytes. The clearest remaining product gap |
| P2-9 | Progress has no `h2`; 11 tiles silently mix all-time and range-scoped numbers | **OPEN** | ~100 bytes net. The mixing is the real defect — tapping "7 d" leaves three tiles unchanged |
| P2-10 | One radio label cancelled the 44 pt rule with an inline `min-height:auto` (~24 px) | **DONE** | Inline override removed; −24 bytes |
| P2-11 | Source documents fetch with no loading state | **PARTIAL** | The crash half is fixed (`modal()` now closes an open dialog before re-showing); the spinner half is open |

## P3 — content and data presentation

| # | Item | Status | Notes |
|---|---|---|---|
| P3-1 | The measure cap missed the jhāna boundary sentence and the whole practice map | **DONE** | Selector widened to the panel; net −4 bytes |
| P3-2 | Hindrance labels truncated to nonsense ("Ill", "Restlessne") | **DONE** | `.split(" ")[0]` removed, slice raised to 14 |
| P3-3 | The dual-series legend named two colours as its only key | **DONE** | Now names position: "left bar / right bar" |
| P3-4 | Progress' empty state told a returning practitioner they had never sat | **DONE** | Branches on the store, not the range |
| P3-5 | Uppercase micro-labels — 11 at once on Progress, 6 on Today | **DONE** | Dropped from `.stat .l` / `.tstat .l`; kept on the two genuinely singular labels |
| P3-6 | Heatmap had no legend and no stated thresholds | **DONE** | Thresholds now named in the caption: none · under 15 · 15–29 · 30–59 · 60+ |
| P3-7 | Heatmap rows are not weekdays; a comment claimed an alignment the code never performs | **PARTIAL** | The false comment is deleted (−20 bytes). The grid still is not weekday-aligned and its rows rotate daily — fixing the maths (~55 bytes) remains open |
| P3-8 | Journal note excerpt truncated twice; second truncation invisible | **OPEN** | ~60 bytes |
| P3-9 | Search has no scope, no result count, no reset | **OPEN** | ~250 bytes — the largest single open item |
| P3-10 | Draft fields have no `<label for>`, and `null` is user-facing copy | **OPEN** | ~200 bytes. Note the *review* form already gets this right |
| P3-11 | `table.kv` uses styled `<td>` where `<th scope="row">` belongs | **OPEN** | ~180 bytes |

## P4 — product character

| # | Item | Status | Notes |
|---|---|---|---|
| P4-1 | During a sit, "absence" was opt-in and had to be re-requested every time | **DONE** | The running state now hides chrome by default; interaction flow asserts the nav is gone |
| P4-2 | The marker log reported your attention back at you mid-sit, and read it aloud | **DONE** | Confirms the tap, keeps no score |
| P4-3 | Third-party retention was never disclosed | **DONE** | One sentence in the AI card |
| P4-4 | The streak cluster opens both home screens: three streak tiles, a target line, a contribution heatmap | **OPEN** | **Owner's call, not a bug.** Gate 0 is the owner's own practice commitment. The presentation-only change would be to keep one continuity number and drop the high score |
| P4-5 | AI provenance is captured, then discarded in session detail and the teacher report | **OPEN** | ~150 bytes. The teacher report prints model-extracted numbers under "All values are the practitioner's own reports" |
| P4-6 | A live percentage recalculates under the thumb moments after the bell | **OPEN** | Show minutes, not percent, at the moment of reflection |
| P4-7 | The practice map introduces gamification vocabulary in order to deny it | **OPEN** | Copy only |
| P4-8 | Onboarding is four screens of prose that the destination screens repeat | **OPEN** | ~−500 bytes if trimmed — one of the few open items that *frees* budget |

---

## What is blocking the rest

Every open item above is small. Together they are roughly **1,700 bytes**, against
**101 bytes** of headroom.

There are three honest ways forward, and the choice is the owner's:

1. **Trim onboarding first** (P4-8). It is the only open item that frees budget (~500
   bytes), and the audit's case for it is independent of size: it teaches material the
   destination screens already carry.
2. **Move the inline self-test corpus behind `?selftest=1`.** It is 61,837 bytes — 18%
   of the file — and ADR-0003 already names this as the remedy for exactly this
   situation. The cost is real and should not be waved through: a `file://` double-click
   could no longer self-verify. That is an ADR amendment, not a cleanup.
3. **Raise the ceiling.** Deliberately *not* done in this pass. The mission's own rule
   applies: a redesign being verbose is not a reason to move the limit, and an ADR whose
   only purpose is "we wanted more CSS" should not be written. Nothing here justifies it
   yet — option 1 or 2 should be exhausted first.

---

# Repair round — independent review blockers

An independent reviewer with fresh eyes ran the build in a browser and returned
**BLOCKED** with five findings. All five are now fixed and re-verified. **Three of the
five were caused by fixes made earlier in this same pass** — recorded that way rather
than presented as pre-existing defects.

| # | Blocker | Cause | Status |
|---|---|---|---|
| B1 | Nav labels frozen at 12px, never responding to user text size — measured 12px at root 16/24/32/64px, and below the app's own `--fs-xs` | **Self-inflicted.** I froze them to stop labels colliding, trading a layout bug for an accessibility exclusion | **FIXED, in two rounds.** Round 1 (bounded clamp + wrap) itself regressed: un-freezing let body's `overflow-wrap:anywhere` fracture "Progress" **mid-word at 320px at default text** (intrinsic 64.9px vs a 62.0px box) — and the gate missed it because `scrollWidth` reads clean when text fits *vertically*. Round 2 is the root-cause fix: `min-width:0` had suppressed flexbox's content-based minimum, so the row could never break. Now `min-width:max-content` floors each button at its full label width and `flex-wrap` reflows the bar to a second row under enlarged text, letting the clamp ceiling rise to 23px (desktop 28px). Verified: every label single-line at root 16–64px, zero true rect intersections, bar within main's reserve. The gate now measures per-label line count, two-axis intersection, and bar height |
| B2 | First-launch onboarding unreachable by keyboard and hidden from screen readers: focus never entered, Tab walked into the app behind it, Escape did nothing | Pre-existing. Root cause: `render()` called `.focus()` while the element was still `hidden`, which silently no-ops | **FIXED** — now a native `<dialog>` + `showModal()`, which supplies focus containment, Escape and focus restore. Escape routes through Skip so the choice persists |
| B3 | "Quiet screen" was a dead control — clicking it mid-sit changed **zero** elements | **Self-inflicted.** Adding `body.running .hide-zen` meant a running sit already hid everything the button would hide | **FIXED** — it is the *maximum* absence mode, so it now also drops the marker bar, marker log, Reset and the elapsed/planned line. Verified: the timer card goes 629px → 466px and 10 elements change state |
| B4 | Three screens scrolled horizontally at 200% text | **Self-inflicted test gap.** My zoom gate only tested the default tab | **FIXED** — root cause was unbreakable long words, not the grids. `overflow-wrap:anywhere` on body, `table-layout:fixed`, `.field{min-width:0}`. All five tabs clean at 320/390px × 150/200% |
| B5 | Chart axis labels clipped and overlapping — a y-axis "100%" at left = −8.9px; 29 of 29 adjacent x-label pairs colliding | Partly self-inflicted: moving chart text to CSS made labels larger than the gutter allowed | **FIXED, in two rounds.** Round 1 (gutters widened, x labels thinned to ~six and staggered onto two baselines) cleared the labels but **introduced NEW-1**: the widened padding applied to both axes, so the vertical span `H−2P` went negative (−6) and every line chart collapsed to a ~1px band drawn *below* the axis with higher values plotting lower — caught by the re-review, because the gates tested clipping and overlap, not geometry. Round 2 splits the paddings (`P` horizontal only, `Q=20` vertical), restoring a 90-unit span. Verified live: 31.5-unit span, all points above the axis, data max at the top. A geometry gate now asserts both properties |

Non-blocking items from the same review that were also fixed:

- **Five duplicate `class` attributes** silently dropping styling. HTML keeps the first and
  discards the rest, with no error. Self-inflicted by the utility-class rewrite, which
  matched `class` and `style` only when adjacent. Now **gated** in the Node runner.
- The Today tile note truncated to `starts with …` at every width from 320 to 430.
- `role="timer"` with no accessible name.
- `<summary>` and `<a>` falling through to the UA focus ring.

Still open from that review, and not claimed as fixed: `role="tablist"` without arrow keys; focus not moved into
the post-sit review; single-select option sets modelled as toggle buttons rather than
radios; two links used as buttons; and the selected tab being invisible under
`forced-colors: active`.

Also from the re-review, open and pre-existing (not caused by these fixes): the
consistency calendar hard-codes its dark-theme hex ramp, so in the light appearance a
"no sit" cell is the *darkest* element on a white card — perceptually inverting the
more-practice-more-ink encoding — and the calendar ignores `prefers-contrast: more`.
The fix is the same CSS-class treatment the other charts got, plus a light ramp;
roughly +150 bytes against 6 free, so it waits for the owner's byte decision.

Fixed since that list was written: the sparkline text equivalent now announces the
**data** maximum, not the axis cap — the ratio chart (which passes an explicit
`yMax: 1` for its axis) previously told a screen-reader user "highest 100%" when the
data peaked far lower. An honesty defect, fixed first.

## Gate coverage added during the repair

Each of these covers a class of bug that reached a reviewer because nothing checked for it:

- Duplicate `class` attributes (Node).
- Whole-script syntax parse (Node) — a syntax error outside the CORE block previously
  passed all 447 tests while the app failed to boot.
- Chart labels clipped by their own viewBox, or overlapping each other.
- Text-zoom sweep across **all five tabs** with every `<details>` open.
- Nothing hidden behind the fixed tab bar, on every screen, at two widths.
- Tab labels neither clipped nor overlapping.
- The dialog gate now waits out the entrance animation — it was reporting 44px buttons as
  43px because the dialog animates from `scale(.98)`.
- The tab gate measures per-label line count via `Range.getClientRects` (a two-line
  single-word label IS the mid-word fracture `scrollWidth` cannot see), true two-axis
  rect intersection (a left/right-only check flags a legitimate wrapped row as overlap),
  and the fixed bar's height against `main`'s bottom reserve.
- Line-chart **geometry**: every polyline must draw entirely above its axis, and varying
  data must span more than 5 units — the two signatures of the NEW-1 failure class,
  which the typography gates were structurally unable to see.
