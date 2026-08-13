# QUICKSTART

From download to first working run in about two minutes. Nothing here needs
an API key until the last section.

## 1. Install (Python 3.10+)

```bash
cd Claude-Knowledge-Graph-Engineering-Kit-v1   # the folder this ZIP extracts to
python3 -m venv .venv && source .venv/bin/activate   # recommended; required on
                                                     # Debian/Ubuntu/Homebrew Pythons
pip install -e ".[dev]"
```

That installs the `kgkit` package, its two dependencies (`pydantic`,
`anthropic`), the test runner (`pytest`, from the `[dev]` extra), and the
`kgkit` command. (On Windows, activate with `.venv\Scripts\activate`.)

## 2. Prove it works — offline

```bash
python -m pytest
```

Expected: `66 passed`, in under a second, with no network access.

## 3. Run the demo — offline

```bash
python -m kgkit.cli demo
```

(Equivalently `kgkit demo`.) Run it from the kit root — it reads
`examples/competitive_intelligence/`. You'll see, in order:

1. a knowledge graph built from six fictional documents
   (10 nodes, 19 edges, 6 sources), saved to
   `examples/competitive_intelligence/output/graph.json` — open it, it's
   plain JSON;
2. grounded answers to factual questions, each citing edge ids — including
   one question ("How many employees…?") the kit correctly **refuses**
   because the graph has no evidence;
3. three specialist analysts (pricing, product, financial) reporting
   cited findings from the same shared graph;
4. a strategic synthesis whose every claim traces to edges, and from edges
   to verbatim quotes across five different documents.

Offline mode replays recorded stage outputs from
`examples/competitive_intelligence/fixtures/` — clearly labeled fixtures,
not live model calls. Everything deterministic (graph assembly, traversal,
validation, citation checking) runs for real.

## 4. Point it at your own documents (needs an API key)

```bash
cp .env.example .env      # put your ANTHROPIC_API_KEY in it, then export it
export ANTHROPIC_API_KEY=sk-ant-...

# any folder of .md/.txt files:
kgkit run --docs path/to/your/docs --out mygraph.json --engine live

# integrity check (verifies every citation quote against your docs):
kgkit validate mygraph.json --docs path/to/your/docs

# ask questions:
kgkit query mygraph.json "Why did X change its pricing?" --engine live
```

Model choice is yours: set `KGKIT_FAST_MODEL` (extraction) and
`KGKIT_QUALITY_MODEL` (resolution/planning/analysis) — see `.env.example`
and [SCALING.md](SCALING.md).

You can also re-run the whole demo live (`kgkit demo --engine live`) to
compare real model output against the recorded fixtures.

## 5. Evaluate before you trust

```bash
kgkit eval run --suite all            # offline, scores the fixture pipeline
kgkit eval run --suite all --engine live   # scores real Claude output
kgkit eval compare evals/runs/<run A>.json evals/runs/<run B>.json
```

See [EVALUATION.md](EVALUATION.md) for the improvement loop.

## Troubleshooting

- **`Could not find the prompts/ directory`** — run commands from the kit
  root, or set `KGKIT_PROMPTS_DIR=/path/to/kit/prompts`.
- **`--engine live needs ANTHROPIC_API_KEY`** — export the key in your
  shell (a `.env` file is not auto-loaded; it's a template for your own
  tooling).
- **`no fixture for stage=... key=...`** — fixture mode only knows the
  demo's recorded inputs. Your own documents and questions need
  `--engine live`.
