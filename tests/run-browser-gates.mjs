/* Sit Tracker — machine-checkable browser gates.
 *
 * These are the checks a machine can actually decide. Anything subjective
 * (does this feel calm? is the hierarchy right?) is deliberately NOT scored here —
 * a fabricated aesthetic number would be worse than no number.
 *
 * Usage:  node tests/run-browser-gates.mjs [baseUrl]
 * Needs:  a static server already serving the repo root, e.g.
 *           npx http-server -p 8099 -s .
 *         and playwright resolvable (NODE_PATH=/opt/node22/lib/node_modules).
 */
import { chromium } from "playwright";

const BASE = process.argv[2] || "http://127.0.0.1:8099";
const APP = BASE + "/sit-tracker-v2.html";

const results = [];
let failed = 0;
function gate(name, ok, detail = "") {
  results.push({ name, ok: !!ok, detail });
  if (!ok) failed++;
  console.log(`${ok ? "  ok  " : "  FAIL"} ${name}${detail ? "  — " + detail : ""}`);
}
function section(t) { console.log("\n=== " + t + " ==="); }

/* WCAG 2.1 relative luminance + contrast ratio, computed over rendered colours. */
const CONTRAST_FN = `
(() => {
  const lin = c => { c /= 255; return c <= 0.04045 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
  const lum = ([r,g,b]) => 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b);
  const parse = s => { const m = String(s).match(/[\\d.]+/g); return m ? m.slice(0,3).map(Number) : null; };
  const alpha = s => { const m = String(s).match(/[\\d.]+/g); return m && m.length > 3 ? Number(m[3]) : 1; };
  const over = (fg, bg, a) => fg.map((c,i) => c*a + bg[i]*(1-a));
  // walk up for the first non-transparent background, compositing as we go
  const bgOf = el => {
    let n = el, stack = [];
    while (n && n.nodeType === 1) {
      const cs = getComputedStyle(n), c = parse(cs.backgroundColor), a = alpha(cs.backgroundColor);
      if (c && a > 0) { stack.push([c,a]); if (a >= 0.999) break; }
      n = n.parentElement;
    }
    let base = [255,255,255];
    for (let i = stack.length-1; i >= 0; i--) base = over(stack[i][0], base, stack[i][1]);
    return base;
  };
  window.__contrast = el => {
    const cs = getComputedStyle(el);
    const fg = parse(cs.color); if (!fg) return null;
    const bg = bgOf(el);
    const f = alpha(cs.color) < 1 ? over(fg, bg, alpha(cs.color)) : fg;
    const l1 = lum(f), l2 = lum(bg);
    return (Math.max(l1,l2) + 0.05) / (Math.min(l1,l2) + 0.05);
  };
  return true;
})()`;

const WIDTHS = [320, 360, 375, 390, 430, 768, 834, 1024, 1280];

async function main() {
  const browser = await chromium.launch();
  const consoleErrors = [];

  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  page.on("console", m => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", e => consoleErrors.push("pageerror: " + e.message));

  await page.goto(APP, { waitUntil: "networkidle" });
  await page.evaluate(CONTRAST_FN);

  /* Dismiss onboarding so the app proper is measurable. */
  const onboardVisible = await page.locator("#onboard:not([hidden])").count();
  if (onboardVisible) {
    for (let i = 0; i < 8; i++) {
      const btns = page.locator("#ob-actions button:visible");
      if (!(await btns.count())) break;
      await btns.last().click().catch(() => {});
      await page.waitForTimeout(120);
      if (!(await page.locator("#onboard:not([hidden])").count())) break;
    }
  }

  section("STRUCTURE");

  const dupIds = await page.evaluate(() => {
    const seen = {}, dup = [];
    document.querySelectorAll("[id]").forEach(e => {
      if (seen[e.id]) dup.push(e.id); else seen[e.id] = 1;
    });
    return dup;
  });
  gate("no duplicate DOM ids", dupIds.length === 0, dupIds.join(", "));

  const danglingAria = await page.evaluate(() =>
    [...document.querySelectorAll("[aria-controls],[aria-labelledby],[aria-describedby]")]
      .flatMap(e => ["aria-controls","aria-labelledby","aria-describedby"]
        .filter(a => e.hasAttribute(a))
        .flatMap(a => e.getAttribute(a).split(/\s+/).filter(Boolean)
          .filter(id => !document.getElementById(id))
          .map(id => e.tagName.toLowerCase() + "#" + (e.id||"?") + " " + a + "->" + id))));
  gate("every aria-controls / labelledby / describedby resolves", danglingAria.length === 0, danglingAria.slice(0,6).join("; "));

  const undefinedVars = await page.evaluate(() => {
    const css = [...document.querySelectorAll("style")].map(s => s.textContent).join("\n");
    const used = new Set([...css.matchAll(/var\(\s*(--[\w-]+)/g)].map(m => m[1]));
    const def = new Set([...css.matchAll(/(--[\w-]+)\s*:/g)].map(m => m[1]));
    return [...used].filter(v => !def.has(v));
  });
  gate("no CSS custom property is used but never defined", undefinedVars.length === 0, undefinedVars.join(", "));

  section("ACCESSIBLE NAMES");

  const unlabelled = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll("input,select,textarea").forEach(el => {
      if (el.type === "hidden") return;
      const id = el.id;
      const has =
        (id && document.querySelector(`label[for="${CSS.escape(id)}"]`)) ||
        el.closest("label") ||
        el.getAttribute("aria-label") ||
        el.getAttribute("aria-labelledby") ||
        el.getAttribute("title");
      if (!has) bad.push((el.tagName + "#" + (id || "(no id)")).toLowerCase());
    });
    return bad;
  });
  gate("every form control has an accessible name", unlabelled.length === 0, unlabelled.slice(0, 8).join(", "));

  const emptyButtons = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll("button,[role=tab],[role=button]").forEach(el => {
      if (el.offsetParent === null && !el.hasAttribute("hidden")) { /* still check */ }
      const name = (el.textContent || "").trim() ||
        el.getAttribute("aria-label") || el.getAttribute("title") || "";
      if (!name) bad.push(el.id || el.className || el.tagName);
    });
    return bad;
  });
  gate("no button without an accessible name", emptyButtons.length === 0, emptyButtons.slice(0, 8).join(", "));

  const genericDialogName = await page.evaluate(() => {
    const d = document.querySelector("dialog");
    if (!d) return null;
    const n = (d.getAttribute("aria-label") || "").trim().toLowerCase();
    return ["dialog", "modal", "window", ""].includes(n) ? (n || "(none)") : null;
  });
  gate("the dialog's accessible name is not a generic placeholder", genericDialogName === null,
    genericDialogName ? `aria-label="${genericDialogName}"` : "");

  section("TOUCH TARGETS (>=44x44, visible interactive elements)");

  const smallTargets = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll("button,a[href],select,summary,input[type=checkbox],input[type=radio],input[type=range],[role=tab],[role=button]").forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;          // not rendered
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.display === "none") return;
      // a small visual control is fine if its label/parent provides the 44pt target
      const lab = el.closest("label");
      const h = Math.max(r.height, lab ? lab.getBoundingClientRect().height : 0);
      const w = Math.max(r.width,  lab ? lab.getBoundingClientRect().width  : 0);
      if (h < 44 || w < 44) {
        bad.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : "." + (el.className||"").toString().split(" ")[0]} ${Math.round(w)}x${Math.round(h)}`);
      }
    });
    return bad;
  });
  gate("every visible interactive target is at least 44x44", smallTargets.length === 0,
    smallTargets.slice(0, 10).join("; ") + (smallTargets.length > 10 ? ` (+${smallTargets.length - 10} more)` : ""));

  section("CONTRAST (rendered, WCAG 2.1)");

  async function contrastScan(label) {
    return await page.evaluate(() => {
      const bad = [];
      const els = document.querySelectorAll("body *");
      for (const el of els) {
        if (!el.offsetParent && el.tagName !== "BODY") continue;
        // only elements with their own visible text node
        const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
        if (!own) continue;
        const cs = getComputedStyle(el);
        if (cs.visibility === "hidden" || cs.opacity === "0") continue;
        const px = parseFloat(cs.fontSize);
        const w = parseInt(cs.fontWeight, 10) || 400;
        // WCAG large text = >=24px, or >=18.66px when bold
        const large = px >= 24 || (px >= 18.66 && w >= 700);
        const need = large ? 3.0 : 4.5;
        const r = window.__contrast(el);
        if (r && r < need) {
          bad.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : (el.className ? "." + String(el.className).split(" ")[0] : "")} ${r.toFixed(2)}:1 (needs ${need}, ${Math.round(px)}px/${w}) "${el.textContent.trim().slice(0, 32)}"`);
        }
      }
      return [...new Set(bad)];
    });
  }

  const cDark = await contrastScan("dark");
  gate("all rendered text meets WCAG contrast (dark appearance)", cDark.length === 0,
    cDark.slice(0, 8).join(" | ") + (cDark.length > 8 ? ` (+${cDark.length - 8} more)` : ""));

  section("APPEARANCE");

  const declaredScheme = await page.evaluate(() =>
    (document.querySelector('meta[name="color-scheme"]') || {}).content || "(none)");
  gate("the document declares support for both appearances", /light/.test(declaredScheme) && /dark/.test(declaredScheme),
    `color-scheme = "${declaredScheme}"`);

  const hasLightCss = await page.evaluate(() =>
    [...document.querySelectorAll("style")].map(s => s.textContent).join("").includes("prefers-color-scheme"));
  gate("the stylesheet defines a light appearance", hasLightCss);

  // Re-render in light and re-scan contrast.
  const lightCtx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "light" });
  const lightPage = await lightCtx.newPage();
  const lightErrors = [];
  lightPage.on("pageerror", e => lightErrors.push(e.message));
  await lightPage.goto(APP, { waitUntil: "networkidle" });
  await lightPage.evaluate(CONTRAST_FN);
  const obL = await lightPage.locator("#onboard:not([hidden])").count();
  if (obL) {
    for (let i = 0; i < 8; i++) {
      const b = lightPage.locator("#ob-actions button:visible");
      if (!(await b.count())) break;
      await b.last().click().catch(() => {});
      await lightPage.waitForTimeout(120);
      if (!(await lightPage.locator("#onboard:not([hidden])").count())) break;
    }
  }
  const bodyBgLight = await lightPage.evaluate(() => getComputedStyle(document.body).backgroundColor);
  const bodyBgDark = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  gate("light and dark actually render different grounds", bodyBgLight !== bodyBgDark,
    `light=${bodyBgLight} dark=${bodyBgDark}`);

  const cLight = await lightPage.evaluate(() => {
    const bad = [];
    for (const el of document.querySelectorAll("body *")) {
      if (!el.offsetParent && el.tagName !== "BODY") continue;
      const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
      if (!own) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.opacity === "0") continue;
      const px = parseFloat(cs.fontSize), w = parseInt(cs.fontWeight, 10) || 400;
      const need = (px >= 24 || (px >= 18.66 && w >= 700)) ? 3.0 : 4.5;
      const r = window.__contrast(el);
      if (r && r < need) bad.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""} ${r.toFixed(2)}:1 (needs ${need}) "${el.textContent.trim().slice(0,28)}"`);
    }
    return [...new Set(bad)];
  });
  gate("all rendered text meets WCAG contrast (light appearance)", cLight.length === 0,
    cLight.slice(0, 8).join(" | ") + (cLight.length > 8 ? ` (+${cLight.length - 8} more)` : ""));
  await lightCtx.close();

  section("RESPONSIVE — no horizontal overflow, no safe-area clipping");

  for (const w of WIDTHS) {
    await page.setViewportSize({ width: w, height: 844 });
    await page.waitForTimeout(90);
    const over = await page.evaluate(() => {
      const de = document.documentElement;
      const bleeding = [];
      if (de.scrollWidth > de.clientWidth + 1) {
        for (const el of document.querySelectorAll("body *")) {
          if (!el.offsetParent) continue;
          const r = el.getBoundingClientRect();
          if (r.right > de.clientWidth + 1 && r.width > 0)
            bleeding.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : (el.className ? "." + String(el.className).split(" ")[0] : "")} right=${Math.round(r.right)}`);
        }
      }
      return { doc: de.scrollWidth, client: de.clientWidth, bleeding: [...new Set(bleeding)].slice(0, 5) };
    });
    gate(`no horizontal overflow at ${w}px`, over.doc <= over.client + 1,
      over.doc > over.client + 1 ? `scrollWidth ${over.doc} > ${over.client}: ${over.bleeding.join(", ")}` : "");
  }
  await page.setViewportSize({ width: 390, height: 844 });

  section("MOTION");

  const reducedCtx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
  const rPage = await reducedCtx.newPage();
  await rPage.goto(APP, { waitUntil: "networkidle" });
  const animatingUnderReduce = await rPage.evaluate(() => {
    const bad = [];
    for (const el of document.querySelectorAll("body *")) {
      const cs = getComputedStyle(el);
      if (cs.animationName && cs.animationName !== "none" && parseFloat(cs.animationDuration) > 0)
        bad.push(`${el.tagName.toLowerCase()}${el.className ? "." + String(el.className).split(" ")[0] : ""}:${cs.animationName}`);
    }
    return [...new Set(bad)];
  });
  gate("no animation runs under prefers-reduced-motion", animatingUnderReduce.length === 0,
    animatingUnderReduce.slice(0, 6).join(", "));
  await reducedCtx.close();

  section("THE ORB CONTRACT");

  const orbRule = await page.evaluate(() => {
    const css = [...document.querySelectorAll("style")].map(s => s.textContent).join("\n");
    return {
      settle: /body\.settling\s+\.orb\s*\{[^}]*animation\s*:\s*orbBreathe/.test(css),
      still: /body\.running:not\(\.settling\)\s+\.orb\s*\{[^}]*animation\s*:\s*none/.test(css)
    };
  });
  gate("the orb animates during settling", orbRule.settle);
  gate("the orb is explicitly still during the sit itself", orbRule.still);

  const orbLive = await page.evaluate(async () => {
    const b = document.body;
    b.classList.add("running");
    b.classList.remove("settling");
    const orb = document.querySelector(".orb");
    const during = getComputedStyle(orb).animationName;
    b.classList.add("settling");
    const settling = getComputedStyle(orb).animationName;
    b.classList.remove("running", "settling");
    return { during, settling };
  });
  gate("live check: orb has no animation while running-not-settling", orbLive.during === "none",
    `animationName=${orbLive.during}`);
  gate("live check: orb animates while settling", orbLive.settling !== "none",
    `animationName=${orbLive.settling}`);

  section("PRIVACY / DATA");

  const exportHygiene = await page.evaluate(() => {
    const h = window.__sitTracker;
    if (!h || !h.STORE) return { ok: false, why: "no test hook" };
    try {
      h.STORE.setSetting("aiKey", "sk-SHOULD-NEVER-APPEAR");
      const json = h.STORE.exportJSON ? h.STORE.exportJSON() : JSON.stringify(h.STORE.load());
      return { ok: json.indexOf("SHOULD-NEVER-APPEAR") === -1, why: "" };
    } catch (e) { return { ok: false, why: e.message }; }
  });
  gate("the API key never appears in an export", exportHygiene.ok, exportHygiene.why);

  const schema = await page.evaluate(() => (window.__sitTracker && window.__sitTracker.CORE)
    ? { v: window.__sitTracker.CORE.SCHEMA_VERSION, app: window.__sitTracker.CORE.APP_VERSION } : null);
  gate("the app exposes its schema and app version", !!schema, schema ? `schema v${schema.v}, app v${schema.app}` : "");

  section("CONSOLE");
  gate("zero console errors during the run", consoleErrors.length === 0,
    consoleErrors.slice(0, 5).join(" | "));

  await browser.close();

  console.log(`\n${results.length - failed}/${results.length} gates passed, ${failed} failed.`);
  if (failed) {
    console.log("\nFAILED GATES:");
    results.filter(r => !r.ok).forEach(r => console.log("  ✗ " + r.name + (r.detail ? "  — " + r.detail : "")));
  }
  process.exit(failed ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(2); });
