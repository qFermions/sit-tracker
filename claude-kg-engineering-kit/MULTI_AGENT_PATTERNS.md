# MULTI_AGENT_PATTERNS — the graph as shared world model

The multi-agent patterns here follow Anthropic's "Building Effective AI
Agents" (see SOURCES.md #2): use the simplest structure that works, and add
agents only where the work genuinely separates.

## Pattern 1 — Orchestrator-workers over a shared graph

This is what `kgkit demo` runs (`src/kgkit/agents/orchestrator.py`):

```
                 persistent knowledge graph (graph.json)
                    ▲            ▲            ▲
              plan+retrieve  plan+retrieve  plan+retrieve
                    │            │            │
             PRICING ANALYST PRODUCT ANALYST FINANCIAL ANALYST
              (one bounded    (one bounded    (one bounded
               question)       question)       question)
                    └────────────┼────────────┘
                                 ▼
                          SYNTHESIZER
              may use ONLY analyst findings + retrieved evidence;
              citations machine-checked against that evidence
```

Why the graph instead of a shared transcript:

- **Workers don't inherit each other's context.** Each analyst gets a
  bounded question and retrieves exactly the evidence it needs — small
  contexts, no cross-contamination, parallelizable.
- **Claims are checkable.** An analyst can only cite edges it actually
  retrieved; the synthesizer can only cite edges some analyst retrieved.
  Fabricated citations are stripped by code, not by another model.
- **Memory outlives the session.** The graph is a JSON file. Tomorrow's
  agents query today's knowledge without re-reading the corpus.

When to add a worker: when a genuinely separate concern needs a bounded
question (the kit's three analysts are configs in `ANALYST_ROLES` — adding
a "regulatory analyst" is three lines plus a fixture/prompt check, not a
new module). When not to: don't create agents for work one query answers.

## Pattern 2 — Evaluator-optimizer, two forms

**Inner form (runtime, bounded):** every semantic stage runs inside a
validate-and-repair loop — attempt, machine-validate (quotes exist,
citations resolve, members are real), re-ask with the specific problems at
most `max_repair_attempts` times, then salvage what verified and report the
rest. Bounded by construction; `tests/test_client.py` proves it.

**Outer form (development loop):** the evaluation harness is the evaluator,
you (or your agent) are the optimizer:

```
baseline eval run  →  inspect failures  →  ONE hypothesis
      ▲                                        │
      └── keep or revert ← compare runs ← change prompt/schema/code
```

See [EVALUATION.md](EVALUATION.md). Run records pin prompt versions, so
`kgkit eval compare` always tells you what actually changed.

## Pattern 3 — Durable state between sessions (harness practice)

Long-running agent work survives on durable artifacts, not long
conversations (see SOURCES.md #3): the graph JSON is the checkpoint, eval
run records are the test gate, and a short recovery-notes file (current
objective, verified state, next action) is the handoff. An overnight agent loop that ingests documents into the graph and
re-runs `kgkit validate` + `kgkit eval run` each cycle inherits all of that
for free.

## Boundaries worth keeping

- The orchestrator (plain code) owns sequencing; agents own judgment.
- Analysts never see each other's reports — convergence happens only at
  the synthesizer, which is exactly where citation checking concentrates.
- The synthesizer interprets, but every load-bearing claim must trace to
  edges. Interpretation without citations does not survive validation.
