# RESEARCH_NOTES — 2026-07-09 run

Primary-source research collected during the platform/product upgrade run.
Each entry: finding → the decision it drove in this repo.

## Platform (Stage 2)

### 1. PWA installability & file:// degradation
Chrome/Android needs HTTPS + manifest (name, 192/512 icons, start_url, standalone) + a
registered service worker; since Chrome 108 offline support is no longer required for the
install prompt. iOS Safari has **no install prompt** — manual Share → Add to Home Screen;
it prefers a 180×180 `apple-touch-icon`; installed iOS web apps run in an **isolated storage
container** (data does not carry over from the Safari tab on install); SW updates on iOS can
lag in standalone mode. On `file://`, service workers/manifests simply don't apply.
**Drove:** manifest.json + sw.js + 192/512/maskable/apple-touch icons, all behind
`location.protocol` feature detection; README documents that installing on iOS starts with
empty storage (export → import to move data in).
Sources: MDN "Making PWAs installable"; developer.chrome.com/blog/update-install-criteria; firt.dev/notes/pwa-ios.

### 2. Storage eviction & persist()
WebKit ITP deletes ALL script-writable storage (localStorage **and** IndexedDB alike) after
7 days of Safari use without visiting the site — switching engines buys nothing. Home-screen
web apps are explicitly exempt (own days-of-use counter). Android Chrome evicts best-effort
origins only under disk pressure (LRU). `navigator.storage.persist()`: Chrome grants
silently by engagement heuristics; exempts from browser-initiated eviction only.
**Drove:** keep localStorage-behind-adapter (ADR-scale decision: IndexedDB deferred until
~5 MB quota is approached); call `persist()` opportunistically on http(s); surface
persistence state + usage estimate + last-export date in Settings; export reminders are the
real durability guarantee.
Sources: webkit.org/blog/10218; MDN Storage quotas & eviction; web.dev/persistent-storage.

### 3. Screen Wake Lock
Chrome 84+, Safari 16.4+, Firefox 126+. iOS bug: broken in *installed home-screen apps*
16.4→18.3, fixed iOS 18.4 (March 2025). Locks auto-release when the document hides;
correct pattern = request in a user gesture, re-request on visibilitychange→visible.
**Drove:** existing acquire-on-start + re-acquire-on-visible pattern kept; README notes
iOS 18.4+ for reliable wake lock in the installed app.
Sources: MDN Screen Wake Lock; caniuse.com/wake-lock; WebKit bug 254545.

### 4. Background timers & audio
Background tabs throttle timers (Chrome: 1/min after 5 min); iOS lock suspends JS and Web
Audio entirely — **no web page can ring a bell on a locked iPhone** without native push.
Honest web timers say so and offer keep-screen-awake. Reconcile on wake from wall-clock
timestamps and ring immediately if the deadline passed.
**Drove:** timer already wall-clock based; added immediate `tick()` on visibilitychange;
added the honest UI note under sit options ("bells may not sound while locked — the elapsed
time stays correct"); catch-up bells capped at 1. Native bell-while-locked is the headline
argument for the future iOS client (ADR-0002).
Sources: Tone.js issue #235; developer.chrome.com/blog/timer-throttling-in-chrome-88; getstillmind.com.

## Product (Stage 4)

### 5. What users praise/complain about in meditation apps
Praise: flexible reliable timer (interval bells), no retention hacking (Insight Timer's
stated stance), CSV export of logs, Medito's free/no-account/offline model. Complaints:
cluttered navigation, accounts/paywalls, buried timers.
**Drove:** timer-first UX stays the top priority; export stays first-class;
"no account, no paywall, offline" recorded as protected differentiators in ROADMAP/ADRs.
Sources: Trustpilot Insight Timer reviews; Insight Timer support docs (CSV export); meditofoundation.org.

### 6. Streak mechanics
Duolingo's streak is the documented manipulative case (loss aversion ~2×, 11:59 PM panic,
guilt notifications; internally controversial). Non-coercive support = missed days as
neutral data, descriptive history, no loss-framed messaging.
**Drove:** added the descriptive "days sat, last 30" metric ("a missed day is data, not
failure"); kept streak numbers because the user's own Gate-0 rule requires a 30-day streak,
but with descriptive, never guilt-framed copy; no notifications of any kind.
Sources: blog.duolingo.com/how-duolingo-streak-builds-habit; helloklarity.com streak-failure analysis.

### 7. Framework migration
Frameworks pay off with deeply shared state, teams, or heavy component reuse. For a
~3,000-line, single-developer, fully-tested app, migration destroys working tested code for
zero user-visible benefit; framework version churn is recurring unpaid maintenance.
Concrete triggers that would change the answer: recurring DOM/state sync bugs, same widget
hand-rolled 3+ times, multiple contributors, virtualized/real-time UI needs.
**Drove:** ADR-0001 recommends staying vanilla with those triggers codified.
Sources: blog.openreplay.com vanilla-vs-frameworks; cortance.com vanilla-js analysis.

### 8. iOS client options
Bell-while-locked is impossible for an installed PWA, trivial for any native shell
(background audio session / local notification with sound). React Native = full rewrite
into churn. SwiftUI = second codebase/language. **Capacitor reuses the existing tested
HTML/JS verbatim** and adds native audio + local notifications; App Review 4.2
(thin-wrapper) risk is real but managed — a fully-offline app with native notifications
passes the airplane-mode test reviewers use.
**Drove:** ADR-0002 designates Capacitor as the recommended path with explicit readiness gates.
Sources: github.com/capacitor-community/native-audio; mobiloud.com App-Review-4.2 analysis.

### 9. Data portability / sync without accounts
Proven: explicit JSON export/import; the exported file in the user's own iCloud/Drive folder
is the sanctioned two-device transport. CRDT libraries are overkill for one user +
append-mostly logs; union-merge by session ID (an implicit G-Set) gives CRDT semantics
without a library. Obsidian's file-sync ecosystem shows plain-file sync works but conflicts
happen — synced file = transport, not truth.
**Drove:** import already union-merges by ID/fingerprint (kept, now documented as the sync
contract in DATA_CONTRACT.md); CRDT libraries explicitly rejected in ROADMAP.
Sources: stephanmiller.com Obsidian sync; dev.to offline-first CRDT complexity; jackson.dev/post/crdts_as_database.

### 10. Teacher-review workflows
Real workflow = live interview; records support the conversation. Documents travel by
email/print/shared file — never a dedicated platform. What a teacher consumes is a short
human-readable summary, not dashboards.
**Drove:** implemented the printable **Teacher report** (last 30 days, plain table +
summary + honesty footer, excludes test data) in History; sharing infrastructure explicitly
rejected in ROADMAP.
Sources: insightwma.org teacher-student meetings; mindfulnessbox.com journal guidance.
