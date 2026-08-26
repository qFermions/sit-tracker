# Apple Design Skill — Provenance

This file records exactly which external design-review skill was used during the
Apple-level design pass on Sit Tracker, where it came from, where it lives, and —
importantly — what it does **not** mean.

## Source

| Field | Value |
|---|---|
| Repository | `https://github.com/dickwu/apple-design-skill` |
| Pinned revision | `d0bac1e765a27a696839e62962e36330ce72f0b7` |
| Revision is | `HEAD` of `refs/heads/main` at the time of install |
| Commit subject | `fix: update repo URLs to dickwu/apple-design-skill` |
| Commit author | Peilin Wu |
| Commit date | Fri Feb 27 15:02:23 2026 −0600 |
| Verified before clone | Yes — `git ls-remote` confirmed the SHA existed at both `HEAD` and `refs/heads/main` prior to cloning |
| Licence | The repository ships **no LICENSE file**. It is used here as a read-only reference for our own review process and nothing from it is redistributed in this repository. |

## Where it is installed

- **Working copy (source of truth):** `/home/user/tools/apple-design-skill`, checked
  out at the pinned SHA in detached-HEAD state.
- **Activation path:** `~/.claude/skills/apple-design` → symlink to the working copy.

Both locations are **outside the Sit Tracker repository and outside the Sit Tracker
runtime**. Nothing from the skill is vendored into `sit-tracker-v2.html`, added to
`sw.js`'s precache list, or introduced as a runtime dependency. Sit Tracker remains a
single-file, zero-dependency, no-build-step offline PWA.

## Installation method (and a correction to the skill's own README)

The skill's `README.md` instructs:

```bash
claude install-skill /path/to/apple-design-skill
```

**That subcommand does not exist in the Claude Code CLI in this environment.**
`claude --help` lists these commands only: `agents`, `auth`, `auto-mode`, `doctor`,
`gateway`, `import`, `install`, `mcp`, `plugin|plugins`, `project`, `setup-token`,
`ultrareview`, `update|upgrade`. There is no `install-skill`.

Skills are installed by placement: a directory containing a `SKILL.md` with YAML
front-matter, located under `~/.claude/skills/<name>/`. The install was therefore done
by symlinking the pinned checkout into that directory, which keeps a single source of
truth (no second copy to drift).

## Proof of installation

| Check | Result |
|---|---|
| Skill directory resolves | `~/.claude/skills/apple-design` → `/home/user/tools/apple-design-skill` |
| Checked-out SHA | `d0bac1e765a27a696839e62962e36330ce72f0b7` |
| `SKILL.md` readable via the install path | Yes (front-matter `name: apple-design`) |
| `references/hig-lookup.md` readable via the install path | Yes (routing table, 80 lines) |
| `references/hig/` exists | Yes |
| **Guideline files actually present** | **53** `.md` files (counted, not assumed) |
| Total corpus size | 4,479 lines / 580 KB across `references/` |
| Registered by the runtime | Yes — appears in the session's available-skills list as `apple-design` |
| Invocable | Yes — invoked successfully; `SKILL.md` loaded and its review method followed |

The count of 53 matches the figure claimed in the skill's own README, verified by
`ls references/hig/*.md | wc -l` rather than taken on trust.

## What this skill is

A third-party, community-authored review skill. Its own `SKILL.md` describes its
contents as guidelines that "originated from Apple's HIG but have been distilled into
**platform-agnostic design rules**." They are a secondary restatement, not Apple's
published text.

## What this skill is **not**

- It is **not** an Apple product, and it is not affiliated with, endorsed by, or
  reviewed by Apple.
- Passing a review conducted with it does **not** mean Apple has certified, approved,
  audited, or blessed Sit Tracker in any way. No such certification exists or is
  claimed.
- It is not a substitute for testing on real hardware. Every accessibility claim in
  this project that came from browser emulation is labelled as such.
- Its guideline text is a distillation. Where this project quotes a guideline, the
  quote is from this skill's reference files — that is what is cited, and it is cited
  as such.

## How it is used in this project

Per the skill's own documented method (`SKILL.md` §"Design Review Process", Step 2),
references are loaded **selectively** — the four foundations (`accessibility.md`,
`color.md`, `layout.md`, `typography.md`) for every review, plus the documents routed
to by `references/hig-lookup.md` for the specific surface under review. The full
53-document corpus is deliberately **not** bulk-loaded; doing so would inflate an
appearance of coverage without improving the audit.

The routing decisions are recorded, document by document, in
`APPLE_HIG_APPLICABILITY_MATRIX.md`.
