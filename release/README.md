# Release procedure — Sit Tracker

The app is one HTML file plus `sw.js`, `manifest.json`, three companion `.md` files and
four generated icons. A release is those ten runtime files, identified by full SHA-256,
reproduced from a manifest. Nothing else may reach a hosted directory.

Prerequisites: Node 22, GNU tar, xz (the packer's only external tools). Browser gates
also need Playwright's Chromium (`CHROME_PATH`, `NODE_PATH` as in the test headers).

## Cut a release (same steps for every future version)

1. Change `sit-tracker-v2.html`; bump `APP_VERSION` and `SW_VERSION` in `sw.js` together
   (the core suite refuses a mismatch). Run `node tests/run-core-tests.mjs sit-tracker-v2.html`.
2. Pack: `node tools/release.mjs pack --out dist/release-vX.Y.Z` — writes seven
   `tp_NN.b64.txt` parts and `release-manifest.json` (every digest, the source commit,
   the runtime allowlist, the `/ → /sit-tracker-v2.html` hosting rewrite recorded separately).
3. Check: `node tools/release.mjs check --manifest dist/release-vX.Y.Z/release-manifest.json --parts dist/release-vX.Y.Z --publish dist/release-vX.Y.Z/public`
   — rebuilds in a temp dir; exit 1 on any corruption or parity failure; the published
   directory is replaced only after every gate passes (previous kept as `public.previous`).
4. Self-test the tooling: `node tools/release.mjs selftest --manifest … --parts …`.
5. Gates on the ASSEMBLED directory (not the source tree):
   `node tests/run-release-gates.mjs dist/release-vX.Y.Z/public <old-client-dir>` plus
   `tests/run-browser-gates.mjs` and `tests/run-interaction-flow.mjs` against a server
   that serves that directory with `/` rewritten to the app.
   The old-client directory is the previous release's runtime files (`git show <tag>:<file>`).
6. Commit `release/vX.Y.Z/release-manifest.json` (parts are reproducible from it).

## Deploy / update the SAME hosted URL (Vercel project `sit-tracker-preview`, team zxc)

Transport is the seven parts. Each part is its own preview deployment whose build command
verifies the part's digest server-side; the final production deployment's build fetches the
parts by their exact deployment URLs (never a moving alias), verifies every digest again,
regenerates the icons, and serves only the allowlisted runtime files. Receipts live in
`~/sit-tracker-vercel-staging/receipts.json`; `node tools/release.mjs resume-plan --manifest … --receipts …`
says which parts still need sending — a part counts as done only when its receipt is for
this release, carries the manifest digest, and its server-side check was observed to pass.
A deployment-creation response is not a passed check.

Rollback: the previous release's manifest and parts are kept (`release/`, `dist/*.previous`);
redeploy them through the same steps. Never repair a broken hosted release by clearing site
data — the service worker only replaces a working installation after a complete precache.

## Moving your data to a new URL (Pages, a deployment URL, the stable entry URL)

Saved data lives in the browser storage of the origin you used; it does not follow you.
1. On the old URL: Settings → Export JSON (full backup). The file never contains the AI key.
2. Open the intended stable URL; complete the first-launch screens.
3. Settings → Import JSON… → review the preview (new / duplicates / invalid) → Import.
4. Verify the Journal shows your records. Importing the same file twice adds nothing.
5. Only then stop using the old URL. (A fixture migration in the gates is not evidence that
   any particular person's real data was migrated.)
