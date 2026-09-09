/* Sit Tracker — release gates. Tests the ACTUAL release directory (the assembled runtime
 * output, not the source tree) served the way hosting serves it: "/" rewrites to the app,
 * everything revalidates, unknown paths 404. Isolated browser profiles, synthetic data only.
 *
 *   served identity      the bytes on the wire are the release bytes; nothing undeclared is served
 *   old client → update  an installed v4.3.0 / schema-5 client (= master) with saved records and
 *                        an active sit receives the candidate through the app's own update notice;
 *                        records migrate to schema 6, the sit survives, stale caches are dropped
 *   failed precache      a candidate whose precache cannot complete never replaces the usable install
 *   origin migration     export on origin A → import on origin B: parity, duplicate policy,
 *                        invalid and future-schema input, and no API key anywhere in the backup
 *   offline reopen       under service-worker control, a NEW page at the root URL works offline
 *   persistence          reload keeps every record exactly once
 *   layout / privacy     no horizontal overflow at phone and desktop widths; every request stays
 *                        on the two test origins; zero console errors outside the broken fixture
 *
 *   mixed-version window an installed PREVIOUS-release worker (start_url-only client, active sit,
 *                        second tab) meets the new release at "/": reproduced, then the new
 *                        document requests its own worker, older-stamped records self-heal, every
 *                        tab lands on the new release, and with the new worker active "/" can no
 *                        longer pull a newer network document
 *
 * Usage: node tests/run-release-gates.mjs <releaseDir> <oldClientDir> [<previousReleaseDir>]
 *   releaseDir         output of `node tools/release.mjs check … --publish <dir>`
 *   oldClientDir       a schema-5 client's runtime files (e.g. `git show fcd0e55:<file>` for each)
 *   previousReleaseDir the previous release's published runtime directory (default dist/release-v4.5.0/public)
 */
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile, mkdtemp, cp, writeFile, rm } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, normalize, extname, resolve, sep } from "node:path";
import { tmpdir } from "node:os";
const req = createRequire(import.meta.url);
const pwRoot = process.env.PLAYWRIGHT_DIR || (process.env.NODE_PATH || "").split(":")[0];
let chromium;
try { ({ chromium } = req("playwright")); } catch { ({ chromium } = req(pwRoot + "/playwright")); }

const RELEASE = resolve(process.argv[2] || "dist/release/public");
const OLD = resolve(process.argv[3] || "");
if (!OLD) { console.error("usage: node tests/run-release-gates.mjs <releaseDir> <oldClientDir>"); process.exit(2); }
const PORT_A = Number(process.env.RG_PORT_A || 8151), PORT_B = Number(process.env.RG_PORT_B || 8152);
const A = `http://127.0.0.1:${PORT_A}`, B = `http://127.0.0.1:${PORT_B}`;
const sha = b => createHash("sha256").update(b).digest("hex");
let failed = 0, n = 0;
const ok = (name, cond, detail = "") => { n++; if (!cond) failed++; console.log(`${cond ? "  ok  " : "  FAIL"} ${name}${detail ? "  — " + detail : ""}`); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- hosting-shaped static servers whose root (and a set of deliberately broken paths) can change
const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json",
  ".md": "text/markdown; charset=utf-8", ".png": "image/png" };
// `down` makes the server refuse every connection: the only honest "network off" for a page
// under service-worker control, because Playwright's setOffline() does not cut the worker's own
// fetches. `hits` counts requests that reached the server, so an offline gate can prove zero.
function serve(port, state) {
  const srv = createServer(async (rq, rs) => {
    state.hits++;
    if (state.down) { rq.socket.destroy(); return; }
    let p = decodeURIComponent(new URL(rq.url, "http://x").pathname);
    if (p === "/") p = "/sit-tracker-v2.html";
    if (state.broken.has(p)) { rs.writeHead(404); return rs.end("broken fixture"); }
    const fp = normalize(join(state.root, p));
    if (!fp.startsWith(state.root + sep)) { rs.writeHead(403); return rs.end(); }
    try {
      const data = await readFile(fp);
      rs.writeHead(200, { "content-type": MIME[extname(fp)] || "application/octet-stream", "cache-control": "public, max-age=0, must-revalidate" });
      rs.end(data);
      state.served++;
    } catch { rs.writeHead(404); rs.end("not found"); }
  });
  srv.keepAliveTimeout = 1;   // no idle keep-alive sockets can outlive a `down` switch
  return new Promise(r => srv.listen(port, "127.0.0.1", () => r(srv)));
}
const stateA = { root: OLD, broken: new Set(), down: false, hits: 0, served: 0 };
const stateB = { root: RELEASE, broken: new Set(), down: false, hits: 0, served: 0 };
const srvA = await serve(PORT_A, stateA);
const srvB = await serve(PORT_B, stateB);

// ---- helpers
const requests = [];
const errors = [];
const http4xx = [];
let phase = "old-client";   // which software is under test when an event arrives
function watch(ctx, tag) {
  ctx.on("request", r => requests.push({ tag, url: r.url() }));
  ctx.on("response", r => { if (r.status() >= 400) http4xx.push({ tag, phase, status: r.status(), url: r.url() }); });
  ctx.on("page", pg => {
    pg.on("pageerror", e => errors.push({ tag, phase, msg: e.message }));
    pg.on("console", m => { if (m.type() === "error") errors.push({ tag, phase, msg: m.text() }); });
  });
}
async function walkOnboarding(page) {
  for (let i = 0; i < 10; i++) {
    if (!(await page.locator("#onboard").isVisible().catch(() => false))) return;
    const b = page.locator("#ob-actions button:visible");
    if (!(await b.count())) return;
    await b.last().click().catch(() => {});
    await page.waitForTimeout(150);
  }
}
async function controlled(page) {
  const probe = () => page.waitForFunction(() => navigator.serviceWorker && !!navigator.serviceWorker.controller, null, { timeout: 8000 }).then(() => true).catch(() => false);
  if (await probe()) return true;
  await page.reload({ waitUntil: "networkidle" });
  return probe();
}
const app = (page, fn, arg) => page.evaluate(fn, arg);
const count = page => app(page, () => window.__sitTracker.STORE.sessions().length);
const cacheNames = page => app(page, () => caches.keys());
const version = page => app(page, () => window.__sitTracker.CORE.APP_VERSION);
const digestVia = (page, path) => app(page, async p => {
  const buf = await (await fetch(p)).arrayBuffer();
  return [...new Uint8Array(await crypto.subtle.digest("SHA-256", buf))].map(b => b.toString(16).padStart(2, "0")).join("");
}, path);
async function importFile(page, text) {
  return app(page, async json => {
    const inp = document.querySelector("#import-file");
    const dt = new DataTransfer();
    dt.items.add(new File([json], "backup.json", { type: "application/json" }));
    inp.files = dt.files;
    inp.dispatchEvent(new Event("change", { bubbles: true }));
    await new Promise(r => setTimeout(r, 500));
    const dlg = document.querySelector("dialog#modal");
    if (!dlg || !dlg.open) return "no-preview";
    const body = dlg.textContent || "";
    const go = [...dlg.querySelectorAll("button")].find(b => /import|confirm|merge|apply/i.test(b.textContent || ""));
    if (!go) { const c = [...dlg.querySelectorAll("button")].find(b => /close|cancel|ok/i.test(b.textContent || "")); if (c) c.click(); return "no-confirm: " + body.slice(0, 120); }
    go.click();
    await new Promise(r => setTimeout(r, 400));
    return "confirmed: " + body.replace(/\s+/g, " ").slice(0, 160);
  }, text);
}
const releaseHtmlSha = sha(readFileSync(join(RELEASE, "sit-tracker-v2.html")));
const releaseSwSha = sha(readFileSync(join(RELEASE, "sw.js")));
const verOf = dir => (readFileSync(join(dir, "sit-tracker-v2.html"), "utf8").match(/APP_VERSION = "([^"]+)"/) || [])[1];
const RELEASE_VER = verOf(RELEASE);   // the candidate under test — never a literal

// synthetic schema-5 records as an installed v4.3.0 client would hold them
const seed = {
  schemaVersion: 5,
  sessions: [
    { id: "syn-1", v: 5, date: "2026-09-01", startTime: "06:30", endTime: "07:00", plannedMin: 30, actualMin: 30, concMin: 12, ratio: 0.4, confidence: "medium", object: "nostril", phase: "foundation", hindrances: {}, qualities: [], nimitta: null, notes: "synthetic release-gate record 1", entrySource: "timer", teacherReview: "none", stability: 3, breathClarity: 3, timelineSource: null, markers: null, timeline: null, manualOverride: false },
    { id: "syn-2", v: 5, date: "2026-09-02", startTime: "06:40", endTime: "07:05", plannedMin: 25, actualMin: 25, concMin: 9, ratio: 0.36, confidence: "low", object: "upperlip", phase: "foundation", hindrances: { restlessness: "mild" }, qualities: ["ease"], nimitta: { category: "none" }, notes: "synthetic release-gate record 2", entrySource: "manual", teacherReview: "none", stability: 2, breathClarity: 3, timelineSource: null, markers: null, timeline: null, manualOverride: false },
    { id: "syn-3", v: 5, date: "2026-09-03", startTime: "07:00", endTime: "07:45", plannedMin: 45, actualMin: 45, concMin: 20, ratio: 0.44, confidence: "high", object: "nostril", phase: "foundation", hindrances: {}, qualities: ["placement", "sustained"], nimitta: { category: "uncertain" }, notes: "synthetic release-gate record 3", entrySource: "timer", teacherReview: "none", stability: 4, breathClarity: 4, timelineSource: null, markers: null, timeline: null, manualOverride: false }
  ],
  settings: { aiEnabled: false, aiEndpoint: "", aiModel: "", aiKey: "sk-SYNTHETIC-KEY-MUST-NEVER-LEAVE-DEVICE", onboarding: { done: true, step: 0 }, guideSeen: true },
  map: null, feedback: [], savedAt: "2026-09-03T08:00:00.000Z"
};
const SECRET = "SYNTHETIC-KEY-MUST-NEVER-LEAVE-DEVICE";

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });

// This section proves the release DIRECTORY through a hosting-shaped server (the rewrite and the
// revalidating cache header are this file's serve()); the real host's rewrite and headers are a
// live gate, verified at the deployed URL, not here.
console.log("\n=== SERVED IDENTITY (release directory through a hosting-shaped server) ===");
stateA.root = RELEASE;
{
  const r = await fetch(A + "/"); const body = Buffer.from(await r.arrayBuffer());
  ok("the root URL serves the release app document byte-for-byte", r.status === 200 && sha(body) === releaseHtmlSha, sha(body).slice(0, 16));
  ok("the app document is served as HTML", /text\/html/.test(r.headers.get("content-type") || ""));
  const s = await fetch(A + "/sw.js");
  ok("sw.js is the release worker and must revalidate (never immutable-cached)", s.status === 200 && sha(Buffer.from(await s.arrayBuffer())) === releaseSwSha && /max-age=0/.test(s.headers.get("cache-control") || ""), s.headers.get("cache-control"));
  for (const [p, t] of [["/manifest.json", "json"], ["/icons/icon-192.png", "png"], ["/icons/apple-touch-icon.png", "png"], ["/PRACTICE_SOURCES.md", "markdown"]]) {
    const x = await fetch(A + p); ok(`${p} resolves with the right type`, x.status === 200 && (x.headers.get("content-type") || "").includes(t), x.headers.get("content-type"));
  }
  const bad = await Promise.all(["/PROJECT_STATE.md", "/tools/release.mjs", "/tests/run-core-tests.mjs", "/.git/HEAD", "/release-manifest.json", "/DATA_CONTRACT.md"].map(p => fetch(A + p).then(x => x.status)));
  ok("private and undeclared paths do not exist in the release directory (a hosting-shaped server 404s them)", bad.every(s => s === 404), bad.join(","));
}
stateA.root = OLD;

console.log("\n=== OLD INSTALLED CLIENT (v4.3.0, schema 5 — what master serves) ===");
const ctxOld = await browser.newContext({ viewport: { width: 390, height: 844 } });
watch(ctxOld, "old→update");
const pOld = await ctxOld.newPage();
await pOld.goto(A + "/", { waitUntil: "networkidle" });
await walkOnboarding(pOld);
await app(pOld, s => localStorage.setItem("jhanaTracker.v2", JSON.stringify(s)), seed);
await pOld.reload({ waitUntil: "networkidle" }); await pOld.waitForTimeout(500);
await walkOnboarding(pOld);
ok("the old client is running", await version(pOld) === "4.3.0");
ok("the old client holds the seeded records", await count(pOld) === 3);
ok("the old client is controlled by its service worker", await controlled(pOld));
ok("the old worker precached under its own version", (await cacheNames(pOld)).includes("sit-tracker-v4.3.0"), (await cacheNames(pOld)).join(","));
// an active sit, started through the real control
await app(pOld, () => { const d = document.querySelector("#sit-config details"); if (d) d.open = true; });
await pOld.locator("#btn-start").click(); await pOld.waitForTimeout(1500);
let timerBefore = await app(pOld, () => localStorage.getItem("jhanaTracker.v2.timer"));
if (!timerBefore) { await pOld.waitForTimeout(2500); timerBefore = await app(pOld, () => localStorage.getItem("jhanaTracker.v2.timer")); }
ok("a sit is in progress and persisted on the old client", !!timerBefore && !!JSON.parse(timerBefore).core, timerBefore ? "phase " + JSON.parse(timerBefore).core.phase : "no timer state");
const startMs = timerBefore ? JSON.parse(timerBefore).core.startMs : null;

console.log("\n=== UPDATE: the candidate lands on the same origin ===");
stateA.root = RELEASE;
await pOld.reload({ waitUntil: "networkidle" }); await pOld.waitForTimeout(600);
ok("before any update check the old app is still what loads", await version(pOld) === "4.3.0");
// the browser checks for a new worker on navigation; trigger that check explicitly (simulated browser update check)
await app(pOld, async () => { const r = await navigator.serviceWorker.getRegistration(); if (r) await r.update(); });
const noticed = await pOld.waitForFunction(() => { const e = document.querySelector("#update-notice"); return e && !e.hidden; }, null, { timeout: 15000 }).then(() => true).catch(() => false);
ok("the app offers the update through its own notice (no forced reload mid-sit)", noticed);
const newCache = await app(pOld, async v => { const c = await caches.open("sit-tracker-v" + v); return (await c.keys()).length; }, RELEASE_VER);
ok("the candidate precached every runtime asset before being offered", newCache >= 9, newCache + " entries");
ok("records are untouched while the update waits", await count(pOld) === 3);
// the property that matters: with the candidate installed AND waiting, a plain reload still serves the old app
await pOld.reload({ waitUntil: "networkidle" }); await pOld.waitForTimeout(500);
const waitingState = await app(pOld, async () => { const r = await navigator.serviceWorker.getRegistration(); return { waiting: !!(r && r.waiting), version: window.__sitTracker.CORE.APP_VERSION }; });
ok("cache-first: the old app keeps serving while the candidate waits (no forced switch on reload)", waitingState.waiting && waitingState.version === "4.3.0", JSON.stringify(waitingState));
const noticedAgain = await pOld.waitForFunction(() => { const e = document.querySelector("#update-notice"); return e && !e.hidden; }, null, { timeout: 8000 }).then(() => true).catch(() => false);
ok("the update notice is offered again on the reload (the waiting worker is remembered)", noticedAgain);
await pOld.locator("#btn-apply-update").click();
const updated = await pOld.waitForFunction(v => window.__sitTracker && window.__sitTracker.CORE.APP_VERSION === v, RELEASE_VER, { timeout: 15000 }).then(() => true).catch(() => false);
await pOld.waitForTimeout(600);
ok("applying the update reloads into the candidate", updated, "version " + await version(pOld).catch(() => "?"));
phase = "candidate";
const envAfter = await app(pOld, () => JSON.parse(localStorage.getItem("jhanaTracker.v2")));
ok("the envelope migrated to schema 6", envAfter.schemaVersion === 6, "schema " + envAfter.schemaVersion);
ok("every record survived the update with its data", envAfter.sessions.length === 3 && envAfter.sessions.map(s => s.id).join() === "syn-1,syn-2,syn-3" && envAfter.sessions[2].concMin === 20 && envAfter.sessions[1].nimitta && envAfter.sessions[1].nimitta.category === "none");
ok("v6 fields are null on migrated records (missing stays missing, never guessed)", envAfter.sessions.every(s => s.practiceMode === null && s.breathSubtle === null && s.pleasantFeeling === null && s.contactWhere === null));
ok("the API key stayed on the device through the update", envAfter.settings.aiKey === seed.settings.aiKey);
const names = await cacheNames(pOld);
ok("the stale cache was dropped and only the candidate's remains", names.length === 1 && names[0] === "sit-tracker-v" + RELEASE_VER, names.join(","));
ok("the worker cache holds the candidate document byte-for-byte", await digestVia(pOld, "/sit-tracker-v2.html") === releaseHtmlSha);
const timerAfter = await app(pOld, () => localStorage.getItem("jhanaTracker.v2.timer"));
ok("the active sit survived the update", !!timerAfter && JSON.parse(timerAfter).core.startMs === startMs, timerAfter ? "same startMs" : "timer state lost");
const recovery = await app(pOld, () => !!window.__sitTracker.TIMER.state() || !document.querySelector("#resume-banner").hidden);
ok("the candidate offers to continue the sit that was in progress", recovery);
await app(pOld, () => { const b = document.querySelector("#btn-resume-timer"); if (b && !document.querySelector("#resume-banner").hidden) b.click(); });
await pOld.waitForTimeout(400);
ok("continuing resumes the sit in the candidate", await app(pOld, () => document.body.classList.contains("running")));
// end the synthetic sit so the rest of the journey has the normal chrome
await app(pOld, async () => { const T = window.__sitTracker.TIMER; if (T.reset) await T.reset(false); });
await pOld.waitForTimeout(400);
ok("the sit can be reset (synthetic — not a saved record)", await count(pOld) === 3 && !(await app(pOld, () => document.body.classList.contains("running"))));

console.log("\n=== FAILED PRECACHE: a broken candidate must not replace a usable installation ===");
const brokenDir = await mkdtemp(join(tmpdir(), "st-broken-"));
await cp(RELEASE, brokenDir, { recursive: true });
await writeFile(join(brokenDir, "sw.js"), readFileSync(join(RELEASE, "sw.js"), "utf8").replace(`SW_VERSION = "v${RELEASE_VER}"`, `SW_VERSION = "v${RELEASE_VER}-broken-fixture"`));
const errMark = errors.length;
stateA.root = brokenDir; stateA.broken = new Set(["/abhinna-6-roadmap.md"]);
await pOld.reload({ waitUntil: "networkidle" }); await pOld.waitForTimeout(400);
await app(pOld, async () => { const r = await navigator.serviceWorker.getRegistration(); if (r) { try { await r.update(); } catch (e) { } } });
await pOld.waitForTimeout(3000);
ok("no update is offered when the precache cannot complete", await app(pOld, () => document.querySelector("#update-notice").hidden));
ok("the usable worker keeps controlling the page", await app(pOld, () => navigator.serviceWorker.controller && /sw\.js$/.test(navigator.serviceWorker.controller.scriptURL)) && await version(pOld) === RELEASE_VER);
await pOld.reload({ waitUntil: "networkidle" }); await pOld.waitForTimeout(500);
ok("the app still opens and keeps its records after the failed update", await version(pOld) === RELEASE_VER && await count(pOld) === 3);
const activeCacheOk = await app(pOld, async v => { const c = await caches.open("sit-tracker-v" + v); return (await c.keys()).length >= 9; }, RELEASE_VER);
ok("the active precache is intact", activeCacheOk);
// Cache.addAll is atomic, so the failed worker leaves an EMPTY cache under its own name (harmless:
// a global caches.match finds nothing in it; the next successful activate deletes it). Its presence
// is the proof that the broken install was actually attempted rather than silently skipped.
const brokenCaches = await app(pOld, async () => { const o = {}; for (const nm of await caches.keys()) if (nm.includes("broken")) o[nm] = (await (await caches.open(nm)).keys()).length; return o; });
ok("the broken install was attempted and left only an empty cache behind", Object.keys(brokenCaches).length === 1 && Object.values(brokenCaches)[0] === 0, JSON.stringify(brokenCaches));
const brokenErrors = errors.splice(errMark).map(e => e.msg);
console.log(`  note  console during the broken fixture (expected: the 404): ${brokenErrors.length ? brokenErrors.join(" | ").slice(0, 200) : "none"}`);
stateA.root = RELEASE; stateA.broken = new Set();
await rm(brokenDir, { recursive: true, force: true });
await pOld.reload({ waitUntil: "networkidle" }); await pOld.waitForTimeout(400);
await app(pOld, async () => { const r = await navigator.serviceWorker.getRegistration(); if (r) await r.update(); });
await pOld.waitForTimeout(1500);
ok("re-checking against the good candidate finds nothing new (identical worker)", await app(pOld, () => document.querySelector("#update-notice").hidden) && (await cacheNames(pOld)).includes("sit-tracker-v" + RELEASE_VER));

console.log("\n=== ORIGIN MIGRATION: export on origin A → import on origin B ===");
await pOld.locator("#tabbtn-settings").click(); await pOld.waitForTimeout(300);
const exported = await app(pOld, async () => {
  let captured = null; const real = URL.createObjectURL;
  URL.createObjectURL = b => { captured = b; return real.call(URL, b); };
  document.querySelector("#btn-export-json").click();
  await new Promise(r => setTimeout(r, 200));
  URL.createObjectURL = real;
  return captured ? await captured.text() : null;
});
const exp = exported ? JSON.parse(exported) : null;
ok("origin A produces a full backup", !!exp && exp.schemaVersion === 6 && exp.sessions.length === 3);
ok("the backup carries no API key (neither the field nor the value)", !!exported && !exported.includes("aiKey") && !exported.includes(SECRET));
ok("origin A still holds its records after exporting", await count(pOld) === 3);

const ctxB = await browser.newContext({ viewport: { width: 390, height: 844 } });
watch(ctxB, "origin-B");
const pB = await ctxB.newPage();
await pB.goto(B + "/", { waitUntil: "networkidle" }); await pB.waitForTimeout(400);
await walkOnboarding(pB);
ok("origin B starts empty (saved data does not follow a new origin by itself)", await count(pB) === 0 && await version(pB) === RELEASE_VER);
await pB.locator("#tabbtn-settings").click(); await pB.waitForTimeout(300);
const imp1 = await importFile(pB, exported);
ok("the backup imports on origin B through the real control with a preview", imp1.startsWith("confirmed"), imp1);
const bSessions = await app(pB, () => window.__sitTracker.STORE.sessions());
const fields = ["id", "date", "startTime", "actualMin", "concMin", "confidence", "object", "notes", "stability", "breathClarity", "entrySource"];
const parity = bSessions.length === 3 && exp.sessions.every(s => { const t = bSessions.find(x => x.id === s.id); return t && fields.every(f => JSON.stringify(t[f]) === JSON.stringify(s[f])) && JSON.stringify(t.nimitta) === JSON.stringify(s.nimitta) && JSON.stringify(t.hindrances) === JSON.stringify(s.hindrances); });
ok("restored records match the contract fields of the source", parity, bSessions.map(s => s.id).join(","));
ok("the restored records are schema-6 stamped", bSessions.every(s => s.v === 6));
ok("no API key arrived on origin B", await app(pB, () => window.__sitTracker.STORE.getSetting("aiKey", "")) === "");
const imp2 = await importFile(pB, exported);
ok("importing the same backup again adds nothing (union by id + fingerprint)", await count(pB) === 3, imp2.slice(0, 90));
const bad1 = await importFile(pB, "{ not json");
ok("invalid JSON is refused and nothing is lost", await count(pB) === 3, bad1.slice(0, 60));
const bad2 = await importFile(pB, JSON.stringify({ schemaVersion: 99, weird: true }));
ok("an unrecognised envelope is refused and nothing is lost", await count(pB) === 3, bad2.slice(0, 60));
const futureRec = { id: "syn-future", date: "2026-09-04", startTime: "07:10", actualMin: 20, concMin: 5, notes: "from a future schema", unknownFutureField: { deep: true } };
const imp3 = await importFile(pB, JSON.stringify({ schemaVersion: 99, sessions: [futureRec, exp.sessions[0]], settings: { aiKey: SECRET } }));
const afterFuture = await app(pB, () => window.__sitTracker.STORE.sessions());
ok("a future-schema backup merges only its new valid record; existing ones stay; nothing is destroyed", afterFuture.length === 4 && afterFuture.some(s => s.id === "syn-future") && exp.sessions.every(s => afterFuture.some(x => x.id === s.id)), imp3.slice(0, 80));
ok("settings inside an imported backup never install an API key", await app(pB, () => window.__sitTracker.STORE.getSetting("aiKey", "")) === "");
// a future-schema envelope already on the device (e.g. a newer client wrote it) must not be destroyed by this version
await app(pB, () => { const e = JSON.parse(localStorage.getItem("jhanaTracker.v2")); e.schemaVersion = 99; e.sessions[0].futureOnly = "keep"; localStorage.setItem("jhanaTracker.v2", JSON.stringify(e)); });
await pB.reload({ waitUntil: "networkidle" }); await pB.waitForTimeout(500);
const futureEnv = await app(pB, () => JSON.parse(localStorage.getItem("jhanaTracker.v2")));
ok("a newer-schema envelope on the device is loaded without destroying records or unknown fields", await count(pB) === 4 && futureEnv.sessions.length === 4 && futureEnv.sessions[0].futureOnly === "keep", "schemaVersion now " + futureEnv.schemaVersion + (futureEnv.schemaVersion === 99 ? " (left as written, not downgraded)" : ""));
await app(pB, () => { const e = JSON.parse(localStorage.getItem("jhanaTracker.v2")); e.schemaVersion = 6; localStorage.setItem("jhanaTracker.v2", JSON.stringify(e)); });
await pB.reload({ waitUntil: "networkidle" }); await pB.waitForTimeout(400);

console.log("\n=== OFFLINE: reopen at the root URL under service-worker control ===");
ok("origin B is controlled by the release worker", await controlled(pB));
await pB.waitForTimeout(500);
// the server refuses every connection AND the context is offline; the gate then requires that
// not a single request reached the server — a page served from the network could not pass
stateB.down = true; const hitsAtOffline = stateB.hits, servedAtOffline = stateB.served;
await ctxB.setOffline(true);
const pOff = await ctxB.newPage();
const offOpened = await pOff.goto(B + "/", { waitUntil: "domcontentloaded" }).then(() => true).catch(() => false);
await pOff.waitForTimeout(800);
const offApp = offOpened && await pOff.locator("#btn-start").count() === 1;
ok("a NEW page at the root URL opens with the server refusing connections", offApp);
// every later probe is guarded so a page that failed to open yields clean FAILs, not an exception
const offEval = async (fn, arg) => { if (!offApp) return null; try { return await pOff.evaluate(fn, arg); } catch (e) { return "threw: " + e.message.split("\n")[0]; } };
ok("records are there offline", await offEval(() => window.__sitTracker.STORE.sessions().length) === 4);
if (offApp) { await pOff.locator("#tabbtn-journal").click(); await pOff.waitForTimeout(300); }
ok("the journal renders offline", offApp && await pOff.locator(".sess-item").count() >= 4);
// the worker answers ANY failed fetch with the app document at status 200 (its navigation
// fallback), so a status check cannot tell a cached asset from the fallback; compare bytes instead
const offlineAssets = {};
for (const p of ["/manifest.json", "/icons/icon-192.png", "/abhinna-practice-manual.md", "/PRACTICE_SOURCES.md", "/abhinna-6-roadmap.md", "/sit-tracker-v2.html"]) {
  const want = sha(readFileSync(join(RELEASE, p)));
  const got = await offEval(async q => {
    const r = await fetch(q); const buf = await r.arrayBuffer();
    return [...new Uint8Array(await crypto.subtle.digest("SHA-256", buf))].map(b => b.toString(16).padStart(2, "0")).join("");
  }, p);
  offlineAssets[p] = got === want ? "release bytes" : "MISMATCH " + String(got).slice(0, 16);
}
ok("runtime assets served offline are the release bytes (not the worker's HTML fallback)", Object.values(offlineAssets).every(v => v === "release bytes"), JSON.stringify(offlineAssets));
if (offApp) { await pOff.locator("#tabbtn-today").click(); await pOff.waitForTimeout(200); }
ok("a sit can be started offline", offApp && await pOff.locator("#btn-start:visible").isEnabled());
await pOff.close();
// the browser may still *attempt* a worker-script update check on navigation; every attempt was
// refused, so nothing the page showed can have come from the network
ok("the server served nothing during the offline journey (every attempt refused; content came from the worker cache)", stateB.served === servedAtOffline, `${stateB.hits - hitsAtOffline} attempt(s) refused, ${stateB.served - servedAtOffline} served`);
await ctxB.setOffline(false);
stateB.down = false;

console.log("\n=== PERSISTENCE: reload keeps every record exactly once ===");
const before = await app(pB, () => window.__sitTracker.STORE.sessions().map(s => s.id).sort());
await pB.reload({ waitUntil: "networkidle" }); await pB.waitForTimeout(400);
const after = await app(pB, () => window.__sitTracker.STORE.sessions().map(s => s.id).sort());
ok("no record is duplicated or lost across a reload", JSON.stringify(before) === JSON.stringify(after) && new Set(after).size === after.length, after.join(","));

console.log("\n=== MIXED-VERSION WINDOW: an installed previous-release worker meets the new release at the root URL ===");
// The client installed from the start_url and never opened "/". After a deploy, its worker misses
// "/" and fetches the NEW document from the network — a new document under an old worker.
const PREV = resolve(process.argv[4] || "dist/release-v4.5.0/public");
const prevVer = verOf(PREV), newVer = RELEASE_VER;
stateA.root = PREV; stateA.broken = new Set();
const ctxM = await browser.newContext({ viewport: { width: 390, height: 844 } });
watch(ctxM, "mixed");
const pM = await ctxM.newPage();
await pM.goto(A + "/sit-tracker-v2.html", { waitUntil: "networkidle" });
await app(pM, s => localStorage.setItem("jhanaTracker.v2", JSON.stringify(s)), seed);
await pM.reload({ waitUntil: "networkidle" }); await pM.waitForTimeout(500);
await walkOnboarding(pM);
ok(`the previous release (v${prevVer}) is installed from its start_url and controlled`, await controlled(pM) && await version(pM) === prevVer);
ok("its worker cached only its own version", JSON.stringify(await cacheNames(pM)) === JSON.stringify(["sit-tracker-v" + prevVer]), (await cacheNames(pM)).join(","));
await app(pM, () => { const d = document.querySelector("#sit-config details"); if (d) d.open = true; });
await pM.locator("#btn-start").click(); await pM.waitForTimeout(1500);
const mixedTimer = await app(pM, () => localStorage.getItem("jhanaTracker.v2.timer"));
ok("a sit is in progress on the installed client", !!mixedTimer && !!JSON.parse(mixedTimer).core);
const pM2 = await ctxM.newPage(); await pM2.goto(A + "/sit-tracker-v2.html", { waitUntil: "networkidle" }); await pM2.waitForTimeout(400);
ok("a second tab of the installed app is open on the same origin", await version(pM2) === prevVer);
stateA.root = RELEASE;
const pM3 = await ctxM.newPage(); await pM3.goto(A + "/", { waitUntil: "networkidle" }); await pM3.waitForTimeout(600);
const mixed = await app(pM3, async () => ({ v: window.__sitTracker.CORE.APP_VERSION, caches: await caches.keys(), controlled: !!navigator.serviceWorker.controller }));
ok(`REPRODUCED: the root URL runs the new document (v${newVer}) under the previous worker`, mixed.v === newVer && mixed.controlled && mixed.caches.includes("sit-tracker-v" + prevVer), JSON.stringify(mixed));
ok("no record is lost in the window", await count(pM3) === 3);
ok("the active sit is untouched in the window", await app(pM3, () => localStorage.getItem("jhanaTracker.v2.timer")) === mixedTimer);
const offeredM = await pM3.waitForFunction(() => { const e = document.querySelector("#update-notice"); return e && !e.hidden; }, null, { timeout: 15000 }).then(() => true).catch(() => false);
ok("the new document's own registration check finds its matching worker and offers the update — no forced reload", offeredM && await app(pM3, () => localStorage.getItem("jhanaTracker.v2.timer")) === mixedTimer);
ok("the previous-version tabs keep working meanwhile", await version(pM2) === prevVer && await count(pM2) === 3);
// SIMULATED: a record stamped by an older schema written during the window (an older client's write)
await app(pM2, () => { const e = JSON.parse(localStorage.getItem("jhanaTracker.v2")); e.sessions.push({ id: "window-rec", v: 5, date: "2026-09-05", startTime: "06:00", actualMin: 20, concMin: 5, notes: "written during the window", entrySource: "manual", teacherReview: "none", stability: null, breathClarity: null, timelineSource: null, markers: null, timeline: null, manualOverride: false, hindrances: {}, qualities: [], nimitta: null }); localStorage.setItem("jhanaTracker.v2", JSON.stringify(e)); });
await pM3.reload({ waitUntil: "networkidle" }); await pM3.waitForTimeout(600);
const healed = await app(pM3, () => JSON.parse(localStorage.getItem("jhanaTracker.v2")).sessions.find(s => s.id === "window-rec"));
ok("a record stamped by an older version is upgraded on the next load (simulated older-client write): stamp current, v6 fields null", !!healed && healed.v === 6 && healed.practiceMode === null && healed.breathSubtle === null && healed.pleasantFeeling === null && healed.contactWhere === null, JSON.stringify({ v: healed && healed.v }));
ok("the healed envelope keeps every record", await count(pM3) === 4);
await pM3.waitForFunction(() => { const e = document.querySelector("#update-notice"); return e && !e.hidden; }, null, { timeout: 15000 }).catch(() => {});
await pM3.locator("#btn-apply-update").click();
const allNew = await Promise.all([pM, pM2, pM3].map(p => p.waitForFunction(v => window.__sitTracker && window.__sitTracker.CORE.APP_VERSION === v, newVer, { timeout: 15000 }).then(() => true).catch(() => false)));
await pM.waitForTimeout(700);
ok("applying the update brings every open tab onto the new release", allNew.every(Boolean), allNew.join(","));
const namesM = await cacheNames(pM);
ok("only the new worker's cache remains", namesM.length === 1 && namesM[0] === "sit-tracker-v" + newVer, namesM.join(","));
ok("records survived the transition", await count(pM) === 4 && await count(pM3) === 4);
ok("the sit that was in progress survived and is offered back", await app(pM, () => localStorage.getItem("jhanaTracker.v2.timer")) === mixedTimer && await app(pM, () => !!window.__sitTracker.TIMER.state() || !document.querySelector("#resume-banner").hidden));
await ctxM.close();
// FORWARD CLOSURE: a FRESH client installs the new worker from its start_url and never visits "/";
// then a newer release lands on the network and the client opens "/" for the first time. The
// worker must answer with its own copy. (The marker sits inside <body>, where a served document
// would carry it; "/" was never cached by this client, so a worker that fell through to the
// network would run the newer document and this gate would fail.)
const futureDir = await mkdtemp(join(tmpdir(), "st-future-"));
await cp(RELEASE, futureDir, { recursive: true });
await writeFile(join(futureDir, "sit-tracker-v2.html"), readFileSync(join(RELEASE, "sit-tracker-v2.html"), "utf8").replace("</body>", "<!--future-fixture--></body>"));
await writeFile(join(futureDir, "sw.js"), readFileSync(join(RELEASE, "sw.js"), "utf8").replace(`SW_VERSION = "v${newVer}"`, 'SW_VERSION = "v9.9.9-future-fixture"'));
stateA.root = RELEASE;
const ctxF = await browser.newContext({ viewport: { width: 390, height: 844 } });
watch(ctxF, "closure");
const pF = await ctxF.newPage();
await pF.goto(A + "/sit-tracker-v2.html", { waitUntil: "networkidle" }); await walkOnboarding(pF);
ok("a fresh client installs the new worker from its start_url only", await controlled(pF) && await version(pF) === newVer);
stateA.root = futureDir;
const pF2 = await ctxF.newPage(); await pF2.goto(A + "/", { waitUntil: "networkidle" }); await pF2.waitForTimeout(600);
const servedOwn = await app(pF2, () => ({ v: window.__sitTracker.CORE.APP_VERSION, future: document.body.innerHTML.includes("future-fixture") }));
ok("first visit to the root URL with a newer document on the network: the worker serves its OWN copy", servedOwn.v === newVer && !servedOwn.future, JSON.stringify(servedOwn));
const offeredF = await pF2.waitForFunction(() => { const e = document.querySelector("#update-notice"); return e && !e.hidden; }, null, { timeout: 15000 }).then(() => true).catch(() => false);
ok("the newer release is still offered through the notice (the normal path)", offeredF);
// navigations that are NOT the app keep their own answer under the new worker
stateA.root = RELEASE;
const rMd = await pF2.goto(A + "/PRACTICE_SOURCES.md", { waitUntil: "load" });
const mdType = await app(pF2, () => document.contentType);
ok("a companion document opened directly is still that document, not the app", !!rMd && rMd.status() === 200 && /markdown|plain/.test(mdType), rMd ? rMd.status() + " " + mdType : "no response");
const errMark404 = errors.length;
const r404 = await pF2.goto(A + "/does-not-exist", { waitUntil: "load" });
ok("an unknown path is still a real 404 under the worker", !!r404 && r404.status() === 404, String(r404 && r404.status()));
errors.splice(errMark404);   // the 404 above is the gate's own deliberate request, not an app error
await rm(futureDir, { recursive: true, force: true });
await ctxF.close();

console.log("\n=== LAYOUT: no horizontal overflow at phone and desktop widths (release directory) ===");
for (const w of [390, 1280]) {
  await pB.setViewportSize({ width: w, height: 900 }); await pB.waitForTimeout(200);
  const overflow = [];
  for (const tab of ["today", "journal", "settings"]) {
    await pB.locator("#tabbtn-" + tab).click(); await pB.waitForTimeout(250);
    const o = await app(pB, () => document.documentElement.scrollWidth - window.innerWidth);
    if (o > 0) overflow.push(tab + ":+" + o);
  }
  ok(`${w}px: Today, Journal and Settings fit the viewport`, overflow.length === 0, overflow.join(" "));
}

console.log("\n=== PRIVACY: every request stays on the test origins; console is clean ===");
const foreign = requests.filter(r => !r.url.startsWith(A + "/") && !r.url.startsWith(B + "/"));
ok(`zero requests left the two test origins (${requests.length} requests observed)`, foreign.length === 0, foreign.slice(0, 3).map(f => f.url).join(" | "));
const oldErrors = errors.filter(e => e.phase === "old-client"), candErrors = errors.filter(e => e.phase !== "old-client");
if (http4xx.length) console.log("  note  4xx responses: " + http4xx.map(x => `${x.phase} ${x.status} ${x.url.replace(/^https?:\/\/[^/]+/, "")}`).join(" | "));
if (oldErrors.length) console.log("  note  console errors while the OLD v4.3.0 client (not the candidate) was running: " + oldErrors.map(e => e.msg).join(" | ").slice(0, 200));
ok("zero console errors from the candidate (outside the broken fixture)", candErrors.length === 0, candErrors.slice(0, 3).map(e => e.phase + ": " + e.msg).join(" | "));

await browser.close();
srvA.close(); srvB.close();
console.log(`\n${n - failed}/${n} release gates passed, ${failed} failed.`);
process.exit(failed ? 1 : 0);
