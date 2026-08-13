# Competitive-intelligence demo

Six **fictional** documents about two invented robot-fleet-software vendors.
Every company, person, and number was invented for this kit, so the corpus
is fully redistributable. The dataset is engineered so that no single
document contains the strategic conclusion — that's the point of the graph.

## What's deliberately hidden in the corpus

| Design trap | Where | What should happen |
|---|---|---|
| Facts spread across sources | price ↑ (d1), capability removed (d2), margin motive (d3), competitor position (d4), customer valuation (d6) | only multi-hop retrieval can assemble the strategic answer |
| Alias | "NRI" (d5) | merges into Northwind Robotics by description, and d5's strategy fact lands on the canonical node |
| Lookalike decoy | "Northwind Logistics" (d5) | must NOT merge with Northwind Robotics |
| Genuine ambiguity | "Project Helios" (d5) | preserved as ambiguous on the graph, not guessed |
| Unanswerable question | employee headcount (q3) | refused with "insufficient evidence", never invented |
| Third-party estimate | Aurora's 55% margin (d6) | carried with `source: Meridian Research estimate` + uncertainty, all the way into the synthesis caveats |

## Run it

```bash
python -m kgkit.cli demo                 # offline, replays fixtures/
python -m kgkit.cli demo --engine live   # real Claude calls (needs API key)
```

Outputs land in `output/` (gitignored): `graph.json` is the persistent
knowledge graph — open it, it's readable JSON.

## Files

- `documents/` — the six source docs (markdown).
- `fixtures/` — recorded stage outputs keyed by stage + input id; these are
  what offline mode replays. They are validated against the same schemas as
  live output and every quote is machine-verified against `documents/`.
- `questions.json` — the demo's questions (q1 strategic, q2 simple,
  q3 unanswerable, q4 multi-hop).
- `expected_answers.json` — human-readable expected outcomes;
  `../../evals/gold_queries.json` is the machine-checked version.
