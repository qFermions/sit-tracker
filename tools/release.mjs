#!/usr/bin/env node
/* Sit Tracker release tool — pack, check, self-test, resume-plan. Node built-ins only,
 * plus GNU tar and xz on PATH (the same two the deterministic packer has always used).
 *
 *   node tools/release.mjs pack        [--src <repo>] --out <dir>
 *   node tools/release.mjs check       --manifest <file> --parts <dir> [--publish <dir>]
 *   node tools/release.mjs selftest    --manifest <file> --parts <dir>
 *   node tools/release.mjs resume-plan --manifest <file> --receipts <file>
 *
 * pack        builds the release from a source tree: a deterministic tar of the
 *             allowlisted SOURCE members, xz-compressed, split into fixed-size parts,
 *             each base64-encoded as a text file, plus release-manifest.json carrying
 *             every full SHA-256 (source files, tar, xz, every part in both forms, the
 *             generated icons, and the complete runtime-output allowlist).
 * check       rebuilds the runtime directory in a fresh temp dir from parts + manifest,
 *             verifying every layer; exits 1 on the first failed gate and never writes a
 *             partial result to --publish (which is replaced only after every gate passes).
 * selftest    runs check against isolated corruption fixtures (missing, duplicate,
 *             out-of-order, truncated, invalid base64, validly-encoded corruption, wrong
 *             expected digest, unreferenced extra file) and the resume-plan fixture.
 *             Fixtures are copies; the originals are never touched.
 * resume-plan lists which parts still need sending: a part is skipped ONLY when its
 *             receipt is for this exact release, marked verified, and carries the
 *             manifest's digest. Unverified receipts are not success.
 */
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import {
  readFileSync, writeFileSync, mkdirSync, mkdtempSync, rmSync, existsSync, readdirSync,
  statSync, lstatSync, copyFileSync, renameSync
} from "node:fs";
import { join, dirname, resolve, relative, sep } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const FORMAT = "sit-tracker-release/1";
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
// Members of the transport tar. The first six are served verbatim; the generator is
// shipped so icons are rebuilt at assembly time instead of being transported as binary.
const SOURCE_MEMBERS = [
  "sit-tracker-v2.html", "sw.js", "manifest.json",
  "PRACTICE_SOURCES.md", "abhinna-practice-manual.md", "abhinna-6-roadmap.md",
  "tools/make-icons.mjs"
];
const RUNTIME_TEXT = SOURCE_MEMBERS.slice(0, 6);
const GENERATED = ["icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/apple-touch-icon.png"];
const ROOT_ENTRY = { "/": "/sit-tracker-v2.html" };   // hosting rewrite; a packaging fact, not source bytes
const PART_BYTES = 13500;
const B64_LINE = 1000;
const TAR_ARGS = ["--sort=name", "--owner=0", "--group=0", "--numeric-owner", "--mtime=2026-01-01 00:00Z", "--format=gnu"];
const XZ_ARGS = ["-9e"];

const sha = b => createHash("sha256").update(b).digest("hex");
const args = parseArgs(process.argv.slice(3));
const cmd = process.argv[2];

class Gate extends Error { constructor(gate, msg) { super(msg); this.gate = gate; } }
const log = (...a) => console.log(...a);

function parseArgs(list) {
  const o = {};
  for (let i = 0; i < list.length; i++) {
    if (list[i].startsWith("--")) { o[list[i].slice(2)] = (list[i + 1] && !list[i + 1].startsWith("--")) ? list[++i] : true; }
  }
  return o;
}
function tmp(prefix) {
  const base = process.env.RELEASE_TMP || tmpdir();
  mkdirSync(base, { recursive: true });
  return mkdtempSync(join(base, prefix));
}
function run(file, argv, opts = {}) { return execFileSync(file, argv, { stdio: ["ignore", "pipe", "pipe"], ...opts }); }
function readVersions(html, sw) {
  const app = (html.match(/APP_VERSION = "([^"]+)"/) || [])[1];
  const schema = Number((html.match(/SCHEMA_VERSION = (\d+)/) || [])[1]);
  const swv = (sw.match(/SW_VERSION = "([^"]+)"/) || [])[1];
  return { version: app, swVersion: swv, schemaVersion: schema };
}
function walk(dir, base = dir, out = []) {
  for (const name of readdirSync(dir).sort()) {
    const p = join(dir, name);
    const st = lstatSync(p);
    if (st.isSymbolicLink()) throw new Gate("output-listing", "symlink in output: " + relative(base, p));
    if (st.isDirectory()) walk(p, base, out);
    else out.push(relative(base, p).split(sep).join("/"));
  }
  return out;
}
function encodeText(bin) {
  const b = bin.toString("base64");
  let s = "";
  for (let i = 0; i < b.length; i += B64_LINE) s += b.slice(i, i + B64_LINE) + "\n";
  return s;
}
function decodeStrict(text, expectBytes) {
  // Buffer.from(..., "base64") silently skips junk; we do not. Every line must be clean
  // standard-alphabet base64, padding only at the very end, and the length must be exact.
  const lines = text.split("\n");
  if (lines[lines.length - 1] !== "") throw new Gate("base64", "part text does not end with a newline");
  lines.pop();
  const joined = lines.join("");
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(joined) || joined.length % 4 !== 0) throw new Gate("base64", "invalid base64 text");
  const bin = Buffer.from(joined, "base64");
  if (bin.toString("base64") !== joined) throw new Gate("base64", "base64 does not round-trip");
  if (bin.length !== expectBytes) throw new Gate("base64", `decoded ${bin.length} bytes, manifest says ${expectBytes}`);
  return bin;
}
function generateIcons(generatorPath, workDir) {
  mkdirSync(join(workDir, "icons"), { recursive: true });
  run(process.execPath, [generatorPath], { cwd: workDir });
  const out = {};
  for (const g of GENERATED) out[g] = readFileSync(join(workDir, g));
  return out;
}

// ---------------------------------------------------------------- pack
function pack() {
  const src = resolve(args.src || REPO_ROOT);
  const out = resolve(args.out || join(REPO_ROOT, "dist", "release"));
  const work = tmp("st-pack-");
  try {
    const stage = join(work, "stage");
    const sourceFiles = [];
    for (const m of SOURCE_MEMBERS) {
      const p = join(src, m);
      if (!existsSync(p)) throw new Gate("source", "missing source member " + m);
      const b = readFileSync(p);
      mkdirSync(dirname(join(stage, m)), { recursive: true });
      copyFileSync(p, join(stage, m));
      sourceFiles.push({ path: m, bytes: b.length, sha256: sha(b) });
    }
    const html = readFileSync(join(src, "sit-tracker-v2.html"), "utf8");
    const sw = readFileSync(join(src, "sw.js"), "utf8");
    const app = readVersions(html, sw);
    if (!app.version || app.swVersion !== "v" + app.version) throw new Gate("versions", `APP_VERSION ${app.version} vs SW_VERSION ${app.swVersion}`);

    // deterministic tar + xz
    run("tar", [...TAR_ARGS, "-cf", join(work, "payload.tar"), ...SOURCE_MEMBERS], { cwd: stage });
    const tarBuf = readFileSync(join(work, "payload.tar"));
    run("xz", [...XZ_ARGS, "-k", join(work, "payload.tar")]);
    const xzBuf = readFileSync(join(work, "payload.tar.xz"));

    // generated icons come from the generator we ship, and must equal the source tree's
    const gen = generateIcons(join(stage, "tools/make-icons.mjs"), join(work, "gen"));
    const generated = [];
    for (const g of GENERATED) {
      const srcIcon = join(src, g);
      if (existsSync(srcIcon) && sha(readFileSync(srcIcon)) !== sha(gen[g])) throw new Gate("icons", "generator output differs from source tree for " + g);
      generated.push({ path: g, bytes: gen[g].length, sha256: sha(gen[g]), generator: "tools/make-icons.mjs" });
    }

    // git identity (best effort — a snapshot without .git records null, not a guess)
    let source = { repo: null, commit: null, branch: null, dirtyMembers: null };
    try {
      const commit = run("git", ["rev-parse", "HEAD"], { cwd: src }).toString().trim();
      const branch = run("git", ["rev-parse", "--abbrev-ref", "HEAD"], { cwd: src }).toString().trim();
      const dirty = run("git", ["status", "--porcelain", "--", ...SOURCE_MEMBERS, ...GENERATED], { cwd: src }).toString().trim();
      const remote = (() => { try { return run("git", ["remote", "get-url", "origin"], { cwd: src }).toString().trim(); } catch { return null; } })();
      source = { repo: remote, commit, branch, dirtyMembers: dirty ? dirty.split("\n") : [] };
    } catch { /* not a git checkout */ }

    // parts
    mkdirSync(out, { recursive: true });
    const parts = [];
    for (let i = 0, idx = 0; i < xzBuf.length; i += PART_BYTES, idx++) {
      const bin = xzBuf.subarray(i, i + PART_BYTES);
      const name = "tp_" + String(idx).padStart(2, "0");
      const text = encodeText(bin);
      writeFileSync(join(out, name + ".b64.txt"), text);
      parts.push({ index: idx, name, textName: name + ".b64.txt", bytes: bin.length, sha256: sha(bin), textBytes: Buffer.byteLength(text), textSha256: sha(Buffer.from(text)) });
    }
    const runtimeFiles = [
      ...RUNTIME_TEXT.map(p => sourceFiles.find(f => f.path === p)).map(f => ({ path: f.path, bytes: f.bytes, sha256: f.sha256 })),
      ...generated.map(g => ({ path: g.path, bytes: g.bytes, sha256: g.sha256 }))
    ];
    const manifest = {
      format: FORMAT,
      app,
      source,
      sourceFiles,
      packaging: {
        tar: "GNU tar " + TAR_ARGS.join(" ") + " -cf payload.tar <members in SOURCE_MEMBERS order>",
        xz: "xz " + XZ_ARGS.join(" "),
        partBytes: PART_BYTES,
        base64: `standard alphabet, ${B64_LINE}-char lines, trailing newline; decoded strictly (no junk, exact length)`,
        ordering: "reassembly order is manifest.parts[] ascending by index; a part is bound to BOTH its name and its digests, so a right-named file with other bytes is corruption, never a reorder; files not named in the manifest are ignored",
        rootEntry: ROOT_ENTRY,
        rootEntryNote: "hosting rewrite of / to the app document; this is deployment configuration, not a change to any source byte"
      },
      payload: { tarBytes: tarBuf.length, tarSha256: sha(tarBuf), xzBytes: xzBuf.length, xzSha256: sha(xzBuf) },
      parts,
      output: { generated, runtimeFiles },
      packedAt: new Date().toISOString(),
      tools: { node: process.version, tar: run("tar", ["--version"]).toString().split("\n")[0], xz: run("xz", ["--version"]).toString().split("\n")[0] }
    };
    writeFileSync(join(out, "release-manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
    log(`packed v${app.version} from ${source.commit || "(no git)"} → ${out}`);
    log(`  tar ${tarBuf.length} B ${manifest.payload.tarSha256}`);
    log(`  xz  ${xzBuf.length} B ${manifest.payload.xzSha256}`);
    log(`  ${parts.length} parts × ${PART_BYTES} B; runtime files: ${runtimeFiles.length}`);
    return 0;
  } finally { rmSync(work, { recursive: true, force: true }); }
}

// ---------------------------------------------------------------- check
function loadManifest(p) {
  const m = JSON.parse(readFileSync(p, "utf8"));
  if (m.format !== FORMAT) throw new Gate("manifest", "unknown manifest format " + m.format);
  for (const k of ["parts", "payload", "sourceFiles", "output"]) if (!m[k]) throw new Gate("manifest", "manifest lacks " + k);
  return m;
}
// Rebuild into workDir/public. Throws Gate on the first failure. Returns gate log.
function assemble(manifest, partsDir, workDir) {
  const gates = [];
  const pass = (g, d) => { gates.push(g + (d ? " — " + d : "")); log("  ok   " + g + (d ? "  (" + d + ")" : "")); };

  // 1. parts, in manifest order, each bound to name + text digest + binary digest
  const chunks = [];
  const seen = new Set();
  for (const p of manifest.parts) {
    if (seen.has(p.name)) throw new Gate("parts", "manifest lists part twice: " + p.name);
    seen.add(p.name);
    const fp = join(partsDir, p.textName);
    if (!existsSync(fp)) throw new Gate("parts", "missing part " + p.textName);
    const text = readFileSync(fp);
    if (text.length !== p.textBytes || sha(text) !== p.textSha256) throw new Gate("parts", `part ${p.name}: text digest mismatch (${text.length} B, ${sha(text)})`);
    const bin = decodeStrict(text.toString("utf8"), p.bytes);
    if (sha(bin) !== p.sha256) throw new Gate("parts", `part ${p.name}: decoded bytes digest mismatch`);
    chunks.push(bin);
  }
  pass("parts", `${manifest.parts.length} parts verified in manifest order`);

  // 2. reassembled compressed payload
  const xz = Buffer.concat(chunks);
  if (xz.length !== manifest.payload.xzBytes || sha(xz) !== manifest.payload.xzSha256) throw new Gate("payload", `xz digest mismatch (${xz.length} B, ${sha(xz)})`);
  writeFileSync(join(workDir, "payload.tar.xz"), xz);
  run("xz", ["-dk", join(workDir, "payload.tar.xz")]);
  const tar = readFileSync(join(workDir, "payload.tar"));
  if (tar.length !== manifest.payload.tarBytes || sha(tar) !== manifest.payload.tarSha256) throw new Gate("payload", "tar digest mismatch");
  pass("payload", `xz ${xz.length} B and tar ${tar.length} B match the manifest`);

  // 3. archive safety: only regular files, only declared paths, nothing that escapes
  const listing = run("tar", ["-tvf", join(workDir, "payload.tar")]).toString().trim().split("\n");
  const declared = new Set(manifest.sourceFiles.map(f => f.path));
  for (const line of listing) {
    const type = line[0];
    const name = line.split(/\s+/).slice(5).join(" ");
    if (type !== "-") throw new Gate("archive", `non-regular member (${type}): ${name}`);
    if (name.startsWith("/") || name.split("/").includes("..") || name.includes("\\")) throw new Gate("archive", "unsafe member path: " + name);
    if (!declared.has(name)) throw new Gate("archive", "undeclared member: " + name);
  }
  if (listing.length !== declared.size) throw new Gate("archive", `archive has ${listing.length} members, manifest declares ${declared.size}`);
  pass("archive", `${listing.length} regular members, all declared, no path escapes`);

  // 4. extract and verify every source member
  const srcDir = join(workDir, "src");
  mkdirSync(srcDir);
  run("tar", ["-xf", join(workDir, "payload.tar"), "-C", srcDir, "--no-same-owner", "--no-same-permissions"]);
  for (const f of manifest.sourceFiles) {
    const b = readFileSync(join(srcDir, f.path));
    if (b.length !== f.bytes || sha(b) !== f.sha256) throw new Gate("source-parity", `${f.path}: digest mismatch`);
  }
  pass("source-parity", `${manifest.sourceFiles.length} extracted files match the manifest digests`);

  // 5. versions inside the artifact agree with the manifest
  const v = readVersions(readFileSync(join(srcDir, "sit-tracker-v2.html"), "utf8"), readFileSync(join(srcDir, "sw.js"), "utf8"));
  if (v.version !== manifest.app.version || v.swVersion !== manifest.app.swVersion || v.schemaVersion !== manifest.app.schemaVersion)
    throw new Gate("versions", `artifact says ${JSON.stringify(v)}, manifest says ${JSON.stringify(manifest.app)}`);
  if (v.swVersion !== "v" + v.version) throw new Gate("versions", "SW_VERSION does not match APP_VERSION");
  pass("versions", `app ${v.version} · sw ${v.swVersion} · schema ${v.schemaVersion}`);

  // 6. generated icons must equal the trusted digests recorded in the manifest
  const gen = generateIcons(join(srcDir, "tools/make-icons.mjs"), join(workDir, "gen"));
  for (const g of manifest.output.generated) {
    if (gen[g.path].length !== g.bytes || sha(gen[g.path]) !== g.sha256) throw new Gate("icons", `${g.path}: generated bytes differ from the manifest`);
  }
  pass("icons", `${manifest.output.generated.length} icons regenerated byte-identically`);

  // 7. assemble the runtime directory and prove its listing is exactly the allowlist
  const pub = join(workDir, "public");
  mkdirSync(join(pub, "icons"), { recursive: true });
  for (const p of RUNTIME_TEXT) copyFileSync(join(srcDir, p), join(pub, p));
  for (const g of manifest.output.generated) writeFileSync(join(pub, g.path), gen[g.path]);
  const have = walk(pub);
  const want = manifest.output.runtimeFiles.map(f => f.path).sort();
  if (JSON.stringify(have) !== JSON.stringify(want)) throw new Gate("output-listing", `runtime dir has [${have}] but the allowlist is [${want}]`);
  for (const f of manifest.output.runtimeFiles) {
    const b = readFileSync(join(pub, f.path));
    if (b.length !== f.bytes || sha(b) !== f.sha256) throw new Gate("output-parity", `${f.path}: digest mismatch in runtime dir`);
  }
  pass("output", `${want.length} runtime files, nothing undeclared, every digest matches`);
  return { gates, pub };
}

function check(opts = args) {
  const manifest = loadManifest(resolve(opts.manifest));
  const partsDir = resolve(opts.parts);
  const work = tmp("st-check-");
  try {
    const { pub } = assemble(manifest, partsDir, work);
    if (opts.publish) {
      const dest = resolve(opts.publish);
      const staging = dest + ".incoming-" + process.pid;
      rmSync(staging, { recursive: true, force: true });
      renameSync(pub, staging);                      // built elsewhere; nothing partial ever lands at dest
      if (existsSync(dest)) {
        const prev = dest + ".previous";
        rmSync(prev, { recursive: true, force: true });
        renameSync(dest, prev);                        // last known-good is kept beside, never overwritten in place
      }
      renameSync(staging, dest);
      log(`  published ${dest} (previous release, if any, kept at ${dest}.previous)`);
    }
    log(`release check PASS — v${manifest.app.version} · xz ${manifest.payload.xzSha256}`);
    return 0;
  } finally { rmSync(work, { recursive: true, force: true }); }
}

// ---------------------------------------------------------------- resume-plan
function resumePlan(opts = args, quiet = false) {
  const manifest = loadManifest(resolve(opts.manifest));
  const receipts = existsSync(resolve(opts.receipts)) ? JSON.parse(readFileSync(resolve(opts.receipts), "utf8")) : { parts: {} };
  const rel = manifest.payload.xzSha256;
  const plan = { release: rel, send: [], skip: [], final: null };
  for (const p of manifest.parts) {
    const r = (receipts.parts || {})[p.name];
    let why;
    if (!r) why = "no receipt";
    else if (r.release !== rel) why = "receipt belongs to another release (" + String(r.release).slice(0, 12) + "…)";
    else if (r.textSha256 !== p.textSha256) why = "receipt digest differs from the manifest";
    else if (r.verified !== true) why = "receipt not verified (a created deployment is not a passed server-side check)";
    if (why) plan.send.push({ part: p.name, why, receipt: r ? { deploymentId: r.deploymentId || null } : null });
    else plan.skip.push({ part: p.name, deploymentId: r.deploymentId || null });
  }
  const f = receipts.final;
  if (plan.send.length) plan.final = { action: "wait", why: `${plan.send.length} part(s) still unsent or unverified` };
  else if (f && f.release === rel && f.verified === true) plan.final = { action: "none", why: "final deployment already verified for this release", deploymentId: f.deploymentId || null };
  else if (f && f.release === rel) plan.final = { action: "verify-first", why: "a final deployment exists for this release but is unverified — verify it before creating another", deploymentId: f.deploymentId || null };
  else plan.final = { action: "deploy", why: "all parts verified; no final deployment for this release" };
  if (!quiet) log(JSON.stringify(plan, null, 2));
  return plan;
}

// ---------------------------------------------------------------- selftest
function selftest() {
  const manifestPath = resolve(args.manifest);
  const partsDir = resolve(args.parts);
  const manifest = loadManifest(manifestPath);
  const work = tmp("st-selftest-");
  let failures = 0, n = 0;
  const expect = (name, fn, wantGate) => {
    n++;
    const fx = join(work, "fx" + n);
    mkdirSync(fx);
    const fparts = join(fx, "parts"); mkdirSync(fparts);
    for (const p of manifest.parts) copyFileSync(join(partsDir, p.textName), join(fparts, p.textName));
    const fman = join(fx, "release-manifest.json");
    copyFileSync(manifestPath, fman);
    const publish = join(fx, "public");
    mkdirSync(publish); writeFileSync(join(publish, "KNOWN-GOOD.txt"), "sentinel");
    try { fn({ parts: fparts, manifest: fman }); } catch (e) { throw new Error("fixture setup failed: " + e.message); }
    let got = null, err = "";
    const realLog = console.log; console.log = () => {};
    try { check({ manifest: fman, parts: fparts, publish }); }
    catch (e) { got = e instanceof Gate ? e.gate : "exception"; err = e.message; }
    finally { console.log = realLog; }
    const sentinelIntact = existsSync(join(publish, "KNOWN-GOOD.txt")) && readdirSync(publish).length === 1;
    const noPartial = !readdirSync(fx).some(x => x.startsWith("public.incoming"));
    let okk;
    if (wantGate === "PASS") okk = got === null && !existsSync(join(publish, "KNOWN-GOOD.txt")) && existsSync(join(publish, "sit-tracker-v2.html")) && existsSync(join(publish + ".previous", "KNOWN-GOOD.txt"));
    else okk = got === wantGate && sentinelIntact && noPartial;
    if (!okk) failures++;
    log(`  ${okk ? "ok  " : "FAIL"} ${name}: expected ${wantGate}, got ${got === null ? "PASS" : got}${err ? " — " + err : ""}${!sentinelIntact && wantGate !== "PASS" ? " [KNOWN-GOOD DISTURBED]" : ""}`);
  };
  const tamper = (fx, name, fn) => writeFileSync(join(fx.parts, name), fn(readFileSync(join(fx.parts, name), "utf8")));
  const editManifest = (fx, fn) => { const m = JSON.parse(readFileSync(fx.manifest, "utf8")); fn(m); writeFileSync(fx.manifest, JSON.stringify(m)); };
  const p = i => manifest.parts[i];

  log("release self-test (fixtures are copies; originals untouched)");
  expect("control: untouched release reconstructs and publishes", () => {}, "PASS");
  expect("missing part", fx => rmSync(join(fx.parts, p(3).textName)), "parts");
  expect("duplicate part (part 01's bytes in part 02's slot)", fx => copyFileSync(join(fx.parts, p(1).textName), join(fx.parts, p(2).textName)), "parts");
  expect("out-of-order (parts 02 and 03 swapped)", fx => {
    const a = readFileSync(join(fx.parts, p(2).textName)), b = readFileSync(join(fx.parts, p(3).textName));
    writeFileSync(join(fx.parts, p(2).textName), b); writeFileSync(join(fx.parts, p(3).textName), a);
  }, "parts");
  expect("truncated part", fx => tamper(fx, p(6).textName, t => t.slice(0, -500)), "parts");
  expect("invalid base64 character", fx => tamper(fx, p(0).textName, t => t.slice(0, 40) + "!" + t.slice(41)), "parts");
  expect("validly-encoded byte corruption", fx => tamper(fx, p(4).textName, t => {
    const bin = Buffer.from(t.replace(/\n/g, ""), "base64"); bin[100] ^= 0x01; return encodeText(bin);
  }), "parts");
  expect("validly-encoded corruption with a forged text digest (binary-layer check must catch it)", fx => {
    tamper(fx, p(4).textName, t => { const bin = Buffer.from(t.replace(/\n/g, ""), "base64"); bin[100] ^= 0x01; return encodeText(bin); });
    const forged = readFileSync(join(fx.parts, p(4).textName));
    editManifest(fx, m => { m.parts[4].textSha256 = sha(forged); m.parts[4].textBytes = forged.length; });
  }, "parts");
  expect("wrong expected payload digest in the manifest", fx => editManifest(fx, m => { m.payload.xzSha256 = "0".repeat(64); }), "payload");
  expect("wrong expected source-file digest in the manifest", fx => editManifest(fx, m => { m.sourceFiles[0].sha256 = "0".repeat(64); }), "source-parity");
  expect("wrong expected icon digest in the manifest", fx => editManifest(fx, m => { m.output.generated[0].sha256 = "0".repeat(64); }), "icons");
  expect("undeclared runtime file in the allowlist", fx => editManifest(fx, m => { m.output.runtimeFiles.push({ path: "PROJECT_STATE.md", bytes: 1, sha256: "0".repeat(64) }); }), "output-listing");
  expect("unreferenced extra file beside the parts is ignored", fx => writeFileSync(join(fx.parts, "tp_99.b64.txt"), "junk\n"), "PASS");

  // resume fixture: only a verified, same-release, digest-matching receipt may skip a part
  n++;
  const rel = manifest.payload.xzSha256;
  const receipts = { parts: {
    tp_00: { release: rel, verified: true, textSha256: p(0).textSha256, deploymentId: "dpl_ok" },
    tp_01: { release: rel, verified: false, textSha256: p(1).textSha256, deploymentId: "dpl_unverified" },
    tp_02: { release: "f".repeat(64), verified: true, textSha256: p(2).textSha256, deploymentId: "dpl_foreign" },
    tp_03: { release: rel, verified: true, textSha256: "0".repeat(64), deploymentId: "dpl_wrongsha" }
  }, final: { release: rel, verified: false, deploymentId: "dpl_final_unverified" } };
  const rp = join(work, "receipts.json"); writeFileSync(rp, JSON.stringify(receipts));
  const plan = resumePlan({ manifest: manifestPath, receipts: rp }, true);
  const sendNames = plan.send.map(s => s.part).join(",");
  const wantSend = manifest.parts.slice(1).map(x => x.name).join(",");
  const okPlan = plan.skip.length === 1 && plan.skip[0].part === "tp_00" && sendNames === wantSend && plan.final.action === "wait";
  if (!okPlan) failures++;
  log(`  ${okPlan ? "ok  " : "FAIL"} resume-plan: skips only the verified same-release part; unverified/foreign/wrong-digest receipts resend; final waits — skip=[${plan.skip.map(s => s.part)}] send=[${sendNames}] final=${plan.final.action}`);
  n++;
  for (const nm of Object.keys(receipts.parts)) receipts.parts[nm] = { release: rel, verified: true, textSha256: manifest.parts.find(x => x.name === nm).textSha256 };
  for (const x of manifest.parts) if (!receipts.parts[x.name]) receipts.parts[x.name] = { release: rel, verified: true, textSha256: x.textSha256 };
  writeFileSync(rp, JSON.stringify(receipts));
  const plan2 = resumePlan({ manifest: manifestPath, receipts: rp }, true);
  const okPlan2 = plan2.send.length === 0 && plan2.final.action === "verify-first";
  if (!okPlan2) failures++;
  log(`  ${okPlan2 ? "ok  " : "FAIL"} resume-plan: all parts verified but final unverified → verify-first, never a blind duplicate deploy — final=${plan2.final.action}`);

  rmSync(work, { recursive: true, force: true });
  log(`release self-test: ${n - failures}/${n} passed, ${failures} failed`);
  return failures ? 1 : 0;
}

// ---------------------------------------------------------------- main
try {
  let code;
  if (cmd === "pack") code = pack();
  else if (cmd === "check") code = check();
  else if (cmd === "selftest") code = selftest();
  else if (cmd === "resume-plan") { resumePlan(); code = 0; }
  else { console.error("usage: node tools/release.mjs pack|check|selftest|resume-plan …"); code = 2; }
  process.exit(code);
} catch (e) {
  if (e instanceof Gate) { console.error(`release check FAIL at gate [${e.gate}]: ${e.message}`); process.exit(1); }
  console.error("release tool error: " + (e.stack || e.message)); process.exit(1);
}
