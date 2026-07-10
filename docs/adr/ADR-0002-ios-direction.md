# ADR-0002 — Future iOS client direction

Status: **Recommended — Capacitor wrapper, when readiness gates pass.** (Paper decision
only; nothing has been scaffolded, purchased, or submitted.)
Date: 2026-07-09

## The requirement that decides everything
A meditation bell must ring while the screen is locked. Research (RESEARCH_NOTES.md §4, §8)
is unambiguous: locked-screen audio is **impossible for any web page or installed PWA on
iOS** (JS and Web Audio suspend on lock), and straightforward for a native shell
(background audio session, or a scheduled local notification with sound).

## Options compared (evidence in RESEARCH_NOTES.md §8)
| Option | Locked bell | Privacy | Reuse of tested code | Solo maintainability | Store risk |
|---|---|---|---|---|---|
| Installed PWA (today) | ✗ | best | 100% | best | n/a |
| Capacitor wrapper | ✓ native plugins | same as now (local) | ~100% (HTML/JS verbatim) | good — one codebase | Guideline 4.2 (managed) |
| React Native / Expo | ✓ | good | ~0% — full rewrite | churny ecosystem | low |
| Native SwiftUI | ✓ best | good | CORE port only | second language/codebase | lowest |

## Recommendation
1. **Now:** the installed PWA is the iOS story — free, private, honest about its bell limit.
2. **When gates pass:** wrap the existing file with Capacitor; add
   `@capacitor-community/native-audio` (or scheduled local notifications) for the
   locked-screen bell; keep localStorage → migrate envelope into the app's WKWebView
   container via the existing JSON export/import (already the documented cross-origin move).

## Readiness gates (all must hold before any code)
- G1: Real-world pain confirmed — the user actually experiences missed bells with the PWA.
- G2: Data contract frozen — DATA_CONTRACT.md stable for ≥1 schema version with no pending renames.
- G3: Web-data migration path tested — export from Safari/PWA → import in wrapper verified.
- G4: Account model decided — remains "none"; App Store listing must not require one.
- G5: Airplane-mode self-test passes with the native bell working (the 4.2 reviewer test).
- G6: Willingness to pay Apple's $99/yr and own App Review risk.

## Explicitly unanswered questions (not disguised as architecture)
- Whether background *audio session* or *scheduled local notification* is the better bell
  mechanism for variable-length sits with interval bells (needs a device spike).
- Whether App Review accepts the app without added "native functionality" beyond
  notifications (evidence is anecdotal both ways).
- Battery behavior of a WKWebView wake lock vs native idle-timer disable.
