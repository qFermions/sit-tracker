import { readFileSync } from "node:fs";
const path = process.argv[2];
const src = readFileSync(path, "utf8");
const start = src.indexOf("/*CORE-START*/");
const end = src.indexOf("/*CORE-END*/");
if (start < 0 || end < 0) { console.error("CORE markers not found"); process.exit(2); }
const core = src.slice(start, end);
const CORE = new Function(core + "\nreturn CORE;")();
const r = CORE.runSelfTests();
console.log(`CORE self-tests: ${r.passed}/${r.total} passed, ${r.failed} failed`);
if (r.failures.length) { console.log("FAILURES:"); r.failures.forEach(f => console.log("  ✗ " + f)); process.exit(1); }
// Payload ceiling gate (ADR-0003): the single-file app must stay under 336 KiB.
const CEILING = 344064;
const bytes = Buffer.byteLength(src, "utf8");
console.log(`payload: ${bytes} bytes (ceiling ${CEILING}, headroom ${CEILING - bytes})`);
if (bytes > CEILING) { console.error(`✗ payload exceeds the ADR-0003 ceiling`); process.exit(1); }
// Orb decision gate (design note §during-a-sit, found dead by review): the static
// rule must not defeat the settle animation while both classes are set in prep.
if (!src.includes("body.running:not(.settling) .orb")) {
  console.error("✗ orb rule regressed: static-during-sit must exclude the settling phase"); process.exit(1);
}
// SW version gate: installed clients only pick up an HTML change when SW_VERSION moves
// with it, so the app version and the SW cache version must always match.
import { dirname, join } from "node:path";
const swSrc = readFileSync(join(dirname(path), "sw.js"), "utf8");
const swVer = (swSrc.match(/SW_VERSION = "v([^"]+)"/) || [])[1];
console.log(`sw: v${swVer} · app: v${CORE.APP_VERSION}`);
if (swVer !== CORE.APP_VERSION) { console.error("✗ sw.js SW_VERSION does not match CORE.APP_VERSION — bump both together"); process.exit(1); }
