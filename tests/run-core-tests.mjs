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
