# Claude Knowledge Graph Engineering Kit for Multi-Agent Systems

Turn a pile of documents into a **permanent, provenance-carrying knowledge
graph** with Claude — then let multiple specialist agents reason over that
graph and answer multi-hop questions where **every claim traces back to a
verbatim quote in a source document**.

Your agent's memory normally dies with its context window. A knowledge graph
makes it permanent, shareable between agents, and checkable by you.

```
Documents → Extraction → Resolution → Assembly → Query
                                         │
                     Pricing / Product / Financial analysts (shared graph)
                                         │
                                  Strategic synthesis
                                         │
                        every claim → edges → document quotes
```

**Try it right now, offline, no API key:**

```bash
pip install -e ".[dev]"   # in a venv; [dev] adds pytest
python -m kgkit.cli demo
python -m pytest          # 66 offline tests
```

The demo builds a graph from six fictional competitive-intelligence
documents, answers questions (including refusing one it has no evidence
for), runs three analyst agents plus a synthesizer, and prints a complete
claims → edges → quotes evidence trail. Offline mode replays recorded stage
outputs (fixtures); add an `ANTHROPIC_API_KEY` and use `--engine live` to
run every stage with real Claude calls.

## Two ways to use this kit

- **Track A — the runnable kit** (this repository). Python 3.10+, the
  official `anthropic` SDK, Pydantic. Ingests folders of `.md`/`.txt`
  documents. Start with [QUICKSTART.md](QUICKSTART.md).
- **Track B — Claude Projects prompt pack.** No code: run the same staged
  workflow manually inside a Claude Project using
  [prompts/claude-project-instructions.md](prompts/claude-project-instructions.md).

## What's in the box

| Path | What it is |
|---|---|
| `src/kgkit/` | The pipeline: extraction, resolution, assembly, query, agents, evaluation |
| `prompts/` | Production prompts for every Claude stage (versioned, editable) |
| `schemas/` | Buyer-readable JSON Schemas exported from the data models |
| `examples/competitive_intelligence/` | Full runnable demo: documents, fixtures, questions, expected answers |
| `evals/` | Gold datasets; `kgkit eval run` writes comparable run records here |
| `tests/` | 66 offline tests (no API key, no network) |

## Reading guide

| Read | When you want |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | fastest path from download to first run |
| [CONCEPTS.md](CONCEPTS.md) | plain-English definitions (node, edge, provenance, multi-hop…) |
| [PIPELINE.md](PIPELINE.md) | how each of the four stages works and why |
| [MULTI_AGENT_PATTERNS.md](MULTI_AGENT_PATTERNS.md) | the graph as shared agent memory |
| [EVALUATION.md](EVALUATION.md) | scoring the system and improving prompts safely |
| [SCALING.md](SCALING.md) | model selection, batching, caching, cost |
| [SOURCES.md](SOURCES.md) | where the methods come from (verified attribution) |
| [LIMITATIONS.md](LIMITATIONS.md) | what this kit does not prove or solve |

## The honesty rules this kit enforces

- Every fact carries a verbatim quote; quotes are machine-verified against
  the source. Unverifiable facts are dropped and reported, never kept.
- Lookalike entities are never merged on string similarity; unresolvable
  ambiguity is preserved on the graph, not forced.
- Answers cite edge ids; citations are machine-checked against retrieved
  evidence. Ungrounded answers become "insufficient evidence".
- If the graph has no evidence, the model is never asked — memory is not
  allowed to fill the gap.

This is an independent product, not affiliated with or endorsed by
Anthropic. See [SOURCES.md](SOURCES.md) for attribution.
