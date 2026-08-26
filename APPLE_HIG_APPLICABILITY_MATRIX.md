# Apple HIG Applicability Matrix

Routing decisions for the 53 guideline documents bundled with the pinned
`apple-design` skill (see `APPLE_SKILL_PROVENANCE.md` for the revision).

The skill's own method (`SKILL.md` §"Design Review Process", Step 2) says: *"Don't try
to load all references at once. Load only the ones relevant to the design being
reviewed."* This matrix is that decision, made explicitly and in advance so the
reasoning is auditable, rather than loading all 53 documents to create an appearance of
coverage.

**Every classification below was checked against the code, not assumed.** Where a
document was ruled out, the ruling is a factual statement about a feature Sit Tracker
does not have — verified by search — not a convenience.

## Legend

- **APPLICABLE** — routed to a real surface; loaded and used in the audit.
- **CONDITIONAL** — a partial or boundary match; loaded only for the specific question
  named in the reason, and its verdict is scoped to that question.
- **NOT APPLICABLE** — Sit Tracker has no such surface. Not loaded.

**MANDATORY FOUNDATION** marks the four the skill requires for *every* review
regardless of surface.

---

## APPLICABLE (29)

| # | Document | Routed to | Reason |
|---|---|---|---|
| 1 | `accessibility.md` | All screens | **MANDATORY FOUNDATION.** Accessibility is the release gate for this pass. |
| 2 | `color.md` | All screens | **MANDATORY FOUNDATION.** The whole token layer (`--bg`…`--err`) is under review. |
| 3 | `layout.md` | All screens | **MANDATORY FOUNDATION.** Safe areas, measure, responsive behaviour 320→1024+. |
| 4 | `typography.md` | All screens | **MANDATORY FOUNDATION.** The type scale and system-font stack are being rebuilt. |
| 5 | `dark-mode.md` | Whole app | The app ships `<meta name="color-scheme" content="dark">` and has **zero** `prefers-color-scheme` CSS. Directly in scope. |
| 6 | `materials.md` | Dialog, toast | Two real `backdrop-filter` glass surfaces exist (lines 146, 151). |
| 7 | `motion.md` | Orb, tabs, dialog, onboarding | Four animations exist; the orb's settle-vs-sit rule is a product contract. |
| 8 | `modality.md` | `<dialog id="modal">`, onboarding overlay, post-sit review | One reused native `<dialog>` (line 611) plus a full-screen `.onboard` overlay. |
| 9 | `feedback.md` | Toast, `aria-live` regions, errors | `#toast` (line 151) and `#timer-live` `role="status"` (line 287). |
| 10 | `entering-data.md` | Post-sit review, Settings, Journal | Substantial forms: duration, bells, reflections, API key, import. |
| 11 | `keyboards.md` | All text/number inputs | On-device keyboard behaviour, `inputmode`, and keyboard avoidance apply on mobile web. |
| 12 | `settings.md` | Settings screen | A real Settings screen with grouping, destructive actions, and a secret. |
| 13 | `launching.md` | App boot, PWA start, resume banner | Launches into a restored state; `#resume-banner` resumes an interrupted sit. |
| 14 | `onboarding.md` | First-open hero + intro | `.onboard` / `.onboard-inner.hero` flow (lines 228–243). |
| 15 | `offering-help.md` | Learn screen, troubleshooting cards | Learn is an explicit help/teaching surface with 8 troubleshooting cards. |
| 16 | `writing.md` | All UI copy | Tone is central to the product thesis; every string is in scope. |
| 17 | `inclusion.md` | Copy, Learn | The app serves a contemplative practice across four traditions; language must not exclude. |
| 18 | `privacy.md` | Storage, export, AI key | Local-first storage plus a BYO API key that must never leak into exports. |
| 19 | `machine-learning.md` | AI journaling adapter | An optional AI feature exists (AI module, line 3239). |
| 20 | `generative-ai.md` | AI journaling adapter | That feature generates text shown to the user; attribution and control rules apply. |
| 21 | `charting-data.md` | Progress | Hand-rolled inline SVG charts (`.chart svg`, line 126). |
| 22 | `searching.md` | Journal | Verified present: `#hist-search` (line 390) plus five filter controls (line 4130). |
| 23 | `gestures.md` | Touch targets, tab bar, scrolling | Touch-first app; the tab bar is a horizontally scrollable strip. |
| 24 | `pointing-devices.md` | Desktop hover states | Real `:hover` rules on tabs, cards, buttons — hover-only affordances are a live risk. |
| 25 | `focus-and-selection.md` | Keyboard navigation | `role="tablist"` and `:focus-visible` exist; keyboard operability is a gate. |
| 26 | `icons.md` | In-UI iconography | Needed to define a legal icon strategy — the mission forbids repackaging Apple's symbol set. |
| 27 | `app-icons.md` | `icons/`, `manifest.json` | Ships 192/512/maskable-512/apple-touch icons. |
| 28 | `printing.md` | Teacher report | A real `@media print` report exists (lines 247–256) and `window.print()` is called (line 5072+). |
| 29 | `playing-audio.md` | Bells | Core to the product: WebAudio start / interval / final bells (AUDIO module, line 2997), plus how audio must behave when the app is backgrounded mid-sit. |

## CONDITIONAL (10)

| # | Document | Scoped question it was loaded for | Reason it is only conditional |
|---|---|---|---|
| 30 | `branding.md` | Does Sit Tracker's own identity stay coherent, and does the redesign avoid imitating Apple's? | The app has a genuine identity (name, ဈာန်, icon, tagline) but no corporate brand programme. |
| 31 | `liquid-glass.md` | Where should glass **stop**? | Loaded as a *constraint*, not a licence. The owner's explicit anti-requirement is "do not turn everything into glass." Two glass surfaces exist and the question is whether they are justified. |
| 32 | `going-full-screen.md` | Is "Quiet screen" the right model? | Quiet screen (`body.zen`, line 61) hides chrome with CSS. Verified: the app never calls `requestFullscreen()` — 0 occurrences. The doc informs the *intent*, not an API usage. |
| 33 | `collaboration-and-sharing.md` | Share card, invite text, export | Verified: there is a canvas share card and invite text, but **no** multi-user collaboration, no shared documents, no presence. Only the sharing half applies. |
| 34 | `file-management.md` | Export / import of JSON and CSV | Verified: exactly one `type="file"` input (import). No document browser, no file provider, no document-based app model. |
| 35 | `images.md` | Share-card canvas and app icons | The app renders no photographic or user-supplied imagery — only generated graphics. |
| 36 | `loading.md` | The one async path | Everything is local and instant; only the optional AI request can take real time. |
| 37 | `multitasking.md` | Backgrounding during a sit | Verified relevant: `wakeLock` is used (4 occurrences) and the timer is timestamp-based to survive sleep and tab-switching. The document's iPad split-view content is not applicable. |
| 38 | `undo-and-redo.md` | Destructive-action safety | Verified: no undo exists, but deletions are gated by `UI.confirmModal` carrying "this cannot be undone" (lines 3871, 3993). Loaded to judge whether confirmation is a sufficient substitute here. |
| 39 | `right-to-left.md` | i18n readiness | Verified: `lang="en"`, no `dir="rtl"`, no RTL locale ships — but `data-i18n` scaffolding exists (9 occurrences), so layout decisions should not actively foreclose RTL. |

## NOT APPLICABLE (14)

Each ruling is a verified absence, not an assumption.

| # | Document | Verified reason |
|---|---|---|
| 40 | `apple-pay.md` | No payments of any kind. The app is free, local, and has no commerce surface. |
| 41 | `in-app-purchase.md` | No purchases, no tiers, no paywall. |
| 42 | `managing-accounts.md` | No accounts and no sign-in — deliberately. Local-first with no server is an architectural commitment (ADR-0001), not a gap. |
| 43 | `managing-notifications.md` | Verified: **0** occurrences of `Notification`. The app never requests notification permission; bells are in-page WebAudio only. |
| 44 | `playing-haptics.md` | Verified: **0** occurrences of `navigator.vibrate`. No haptics are produced. |
| 45 | `playing-video.md` | No video element and no video playback anywhere. |
| 46 | `maps.md` | No maps and no location. Verified **0** occurrences of `geolocation`. The app's "Practice Map" is a metaphor for a progression of practice stages — classifying this document as applicable on the strength of the word "map" would be exactly the fabricated coverage this matrix exists to prevent. |
| 47 | `augmented-reality.md` | No AR, no 3D, no camera. Verified **0** occurrences of `getUserMedia`. |
| 48 | `game-controls.md` | Not a game; no game-controller input. |
| 49 | `drag-and-drop.md` | No drag-and-drop affordance anywhere in the UI. |
| 50 | `apple-pencil-and-scribble.md` | No stylus, drawing, or handwriting input. Text entry is plain `<textarea>` / `<input>`. |
| 51 | `live-viewing-apps.md` | No live events, broadcasts, or real-time shared viewing. |
| 52 | `ratings-and-reviews.md` | The app never prompts for a rating or review; it is not distributed through a store. |
| 53 | `sf-symbols.md` | Sit Tracker must **not** use Apple's proprietary symbol set — bundling or redrawing it is an explicit anti-requirement. The icon strategy is governed by `icons.md` instead. Ruled out on purpose, not by omission. |

**Tally: 29 applicable + 10 conditional + 14 not applicable = 53.**

---

## Load discipline

- Loaded and read for the audit: the 29 applicable documents, plus the 10 conditional
  ones **only** against the scoped question named above.
- Deliberately not loaded: the 14 not-applicable documents.
- The four mandatory foundations are re-loaded for each slice of the implementation
  work, not once at the start.

Coverage is therefore **39 of 53 documents consulted (74%)**, with the remaining 14
excluded for a verified factual reason each. That percentage is a description of this
app's surface area — not a score to be maximised.
