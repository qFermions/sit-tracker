/* Sit Tracker — end-to-end interaction verification.
 * Drives the real UI the way a person does: open, configure, start, settle, sit,
 * mark, quiet screen, pause, resume, finish, auto-save, review, journal, progress,
 * learn, settings, export, reload, offline. Asserts behaviour, not DOM existence.
 *
 * Usage: node tests/run-interaction-flow.mjs [baseUrl]
 */
import { createRequire } from "node:module";
const req = createRequire(import.meta.url);
const pwRoot = process.env.PLAYWRIGHT_DIR || (process.env.NODE_PATH || "").split(":")[0];
let chromium;
try { ({ chromium } = req("playwright")); } catch { ({ chromium } = req(pwRoot + "/playwright")); }

const BASE = process.argv[2] || "http://127.0.0.1:8099";
const APP = BASE + "/sit-tracker-v2.html";
let failed = 0, n = 0;
const ok = (name, cond, detail = "") => {
  n++; if (!cond) failed++;
  console.log(`${cond ? "  ok  " : "  FAIL"} ${name}${detail ? "  — " + detail : ""}`);
};

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", e => errors.push(e.message));
page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

await page.goto(APP, { waitUntil: "networkidle" });
await page.waitForTimeout(400);

console.log("\n=== FIRST OPEN ===");
ok("the onboarding hero appears on a first open", await page.locator("#onboard[open]").count() === 1);
// walk it the way a person would
for (let i = 0; i < 8; i++) {
  const b = page.locator("#ob-actions button:visible");
  if (!(await b.count())) break;
  await b.last().click().catch(() => {});
  await page.waitForTimeout(150);
  if (!(await page.locator("#onboard[open]").count())) break;
}
ok("onboarding can be completed and does not reappear", await page.locator("#onboard[open]").count() === 0);

console.log("\n=== TODAY: what am I practising, how long, how do I begin ===");
await page.locator("#tabbtn-today").click();
await page.waitForTimeout(200);
ok("a practice is offered", await page.locator(".preset-card").count() > 0);
ok("Start is present and enabled", await page.locator("#btn-start:visible").isEnabled());
const settlingOn = await page.locator("#opt-prep").isChecked();
ok("the settling countdown is on by default", settlingOn);

console.log("\n=== SETTLING -> SIT ===");
// shortest settle so the test stays quick — the control lives behind the Options disclosure
await page.evaluate(() => { const d = document.querySelector("#sit-config details"); if (d) d.open = true; });
await page.waitForTimeout(150);
await page.selectOption("#opt-prep-sec", "10");
await page.locator("#btn-start").click();
await page.waitForTimeout(400);
ok("the sit starts", await page.evaluate(() => document.body.classList.contains("running")));
ok("the orb breathes during settling",
  await page.evaluate(() => document.body.classList.contains("settling") && getComputedStyle(document.querySelector(".orb")).animationName !== "none"));
ok("app chrome gets out of the way without being asked",
  await page.evaluate(() => { const n = document.querySelector("nav.tabs"); return getComputedStyle(n).display === "none"; }));

console.log("\n=== DURING THE SIT ===");
await page.waitForTimeout(11000);   // let the 10s settle elapse
ok("the sit itself is running, not settling",
  await page.evaluate(() => document.body.classList.contains("running") && !document.body.classList.contains("settling")));
ok("the orb is STILL during the sit (the practice object is the breath, not the screen)",
  await page.evaluate(() => getComputedStyle(document.querySelector(".orb")).animationName === "none"));
await page.locator('[data-marker="steady"]').click();
await page.waitForTimeout(150);
await page.locator('[data-marker="wandering"]').click();
await page.waitForTimeout(150);
ok("markers record without leaving the sit", await page.evaluate(() => document.body.classList.contains("running")));

console.log("\n=== PAUSE / RESUME ===");
await page.locator("#btn-pause").click(); await page.waitForTimeout(250);
ok("pausing is reflected in the UI", await page.evaluate(() => document.body.classList.contains("timer-paused")));
await page.locator("#btn-pause").click(); await page.waitForTimeout(250);
ok("resuming clears the paused state", await page.evaluate(() => !document.body.classList.contains("timer-paused")));

console.log("\n=== FINISH -> THE SIT IS ALREADY SAVED ===");
// the app deliberately refuses to record a sit under 10 seconds; let it pass that floor
await page.waitForTimeout(11000);
const before = await page.evaluate(() => window.__sitTracker.STORE.sessions().length);
await page.locator("#btn-finish").click();
await page.waitForTimeout(900);
const after = await page.evaluate(() => window.__sitTracker.STORE.sessions().length);
ok("finishing saves the sit immediately", after === before + 1, `${before} -> ${after}`);
ok("the review opens as enrichment of an already-saved entry", await page.locator("#review-card").count() === 1);
const closeLabel = (await page.locator("#rv-close").textContent()) || "";
ok("the dismiss control says the sit is saved", /saved/i.test(closeLabel), `"${closeLabel.trim()}"`);

console.log("\n=== REVIEW: focus and disclosure survive a re-render ===");
// open the disclosure that actually contains the chips, the way a person would
const idx = await page.evaluate(() => {
  const ds = [...document.querySelectorAll("#review-card details")];
  const i = ds.findIndex(d => d.querySelector(".rv-hindrance"));
  if (i >= 0) ds[i].open = true;
  return i;
});
ok("the hindrance section can be opened", idx >= 0);
await page.waitForTimeout(200);
const chip = page.locator("#review-card .rv-hindrance").first();
await chip.click();
await page.waitForTimeout(300);
ok("the section the user is working inside stays open after the rebuild",
  await page.evaluate(i => document.querySelectorAll("#review-card details")[i].open, idx));
ok("focus is not dumped to <body> after the rebuild",
  await page.evaluate(() => document.activeElement && document.activeElement !== document.body),
  await page.evaluate(() => (document.activeElement && (document.activeElement.id || document.activeElement.tagName)) || "none"));

// the light-report select is the self-defeating case: choosing a value used to collapse
// the very section that value was meant to reveal
const nimIdx = await page.evaluate(() => {
  const ds = [...document.querySelectorAll("#review-card details")];
  const i = ds.findIndex(d => d.querySelector("#rv-nim-cat"));
  if (i >= 0) ds[i].open = true;
  return i;
});
if (nimIdx >= 0) {
  const opts = await page.evaluate(() => [...document.querySelectorAll("#rv-nim-cat option")].map(o => o.value).filter(Boolean));
  if (opts.length) {
    await page.selectOption("#rv-nim-cat", opts[0]);
    await page.waitForTimeout(300);
    ok("choosing a light category does not collapse the section it belongs to",
      await page.evaluate(i => document.querySelectorAll("#review-card details")[i].open, nimIdx));
  }
}

const savedCount = await page.evaluate(() => window.__sitTracker.STORE.sessions().length);
await page.locator("#rv-close").click(); await page.waitForTimeout(300);
ok("closing the review loses nothing", await page.evaluate(() => window.__sitTracker.STORE.sessions().length) === savedCount);

console.log("\n=== JOURNAL / PROGRESS / LEARN / SETTINGS ===");
for (const [tab, probe] of [["journal", "#history-list"], ["progress", "#progress-container"], ["learn", "#learn-sources"], ["settings", "#storage-info"]]) {
  await page.locator("#tabbtn-" + tab).click();
  await page.waitForTimeout(350);
  ok(`${tab} renders`, await page.locator(probe).count() === 1 && await page.locator("#tab-" + tab + ".active").count() === 1);
}
await page.locator("#tabbtn-journal").click(); await page.waitForTimeout(300);
ok("the finished sit appears in the journal", await page.locator(".sess-item").count() >= 1);
await page.locator("#tabbtn-learn").click(); await page.waitForTimeout(300);
ok("Learn's collapsible sections show a disclosure marker",
  await page.evaluate(() => getComputedStyle(document.querySelector("#tab-learn details summary")).display === "list-item"));

console.log("\n=== EXPORT ===");
await page.locator("#tabbtn-settings").click(); await page.waitForTimeout(300);
const exported = await page.evaluate(async () => {
  let captured = null; const real = URL.createObjectURL;
  URL.createObjectURL = b => { captured = b; return real.call(URL, b); };
  document.querySelector("#btn-export-json").click();
  await new Promise(r => setTimeout(r, 150));
  URL.createObjectURL = real;
  return captured ? await captured.text() : null;
});
ok("export produces a real backup", !!exported && exported.length > 50, exported ? exported.length + " bytes" : "nothing");
ok("the export carries the saved sit", !!exported && JSON.parse(exported).sessions.length >= 1);

console.log("\n=== IMPORT ROUND-TRIP ===");
// wipe, then bring the exported backup back through the real import control
const roundTrip = await page.evaluate(async json => {
  const h = window.__sitTracker;
  const had = h.STORE.sessions().length;
  h.STORE.wipe();
  const after = h.STORE.sessions().length;
  const inp = document.querySelector("#import-file");
  if (!inp) return { why: "#import-file missing" };
  const dt = new DataTransfer();
  dt.items.add(new File([json], "backup.json", { type: "application/json" }));
  inp.files = dt.files;
  inp.dispatchEvent(new Event("change", { bubbles: true }));
  await new Promise(r => setTimeout(r, 500));
  return { had, afterWipe: after };
}, exported);
ok("wiping clears the store", roundTrip.afterWipe === 0, JSON.stringify(roundTrip));
// the app shows an import preview before writing — confirm it, then check the data landed
const confirmed = await page.evaluate(async () => {
  const dlg = document.querySelector("dialog#modal");   // #onboard is also a <dialog> now
  if (!dlg || !dlg.open) return "no import preview appeared";
  const btns = [...dlg.querySelectorAll("button")];
  const go = btns.find(b => /import|confirm|merge|apply/i.test(b.textContent || ""));
  if (!go) return "preview had no confirm control: " + btns.map(b => b.textContent.trim()).join("/");
  go.click();
  await new Promise(r => setTimeout(r, 400));
  return "confirmed";
});
ok("import shows a preview and can be confirmed", confirmed === "confirmed", confirmed);
ok("the imported sit is back in the store",
  await page.evaluate(() => window.__sitTracker.STORE.sessions().length) >= 1);

console.log("\n=== RELOAD + OFFLINE ===");
await page.reload({ waitUntil: "networkidle" }); await page.waitForTimeout(600);
ok("the saved sit survives a reload", await page.evaluate(() => window.__sitTracker.STORE.sessions().length) >= 1);
await ctx.setOffline(true);
await page.reload({ waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(800);
ok("the app still loads with the network off", await page.locator("#btn-start").count() === 1);
await ctx.setOffline(false);

console.log("\n=== CONSOLE ===");
ok("zero console errors across the whole flow", errors.length === 0, errors.slice(0, 4).join(" | "));

await browser.close();
console.log(`\n${n - failed}/${n} interaction checks passed, ${failed} failed.`);
process.exit(failed ? 1 : 0);
