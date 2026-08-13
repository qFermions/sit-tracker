# CONCEPTS — the eight ideas in this kit, in plain English

Each concept is defined next to the real thing it names in this kit, so you
can open the file and look at one while reading.

## Entity

A real-world thing worth tracking: a company, a product, a person, a
capability. In extraction output an entity is still just a **mention** — the
name exactly as one document wrote it ("NRI", "Northwind Robotics, Inc.").
*Look at:* `mentions` in `examples/competitive_intelligence/fixtures/extraction/d1-pricing-update.json`.

## Relation

A fact connecting a subject to an object: *Fleet Pro — priced_at — $79 per
month*. The object can be another entity or a plain value (money, percent,
date). *Look at:* `facts` in the same fixture file.

## Node

An entity after resolution: one canonical name, its aliases, and where it
was seen. "Northwind Robotics", "Northwind Robotics, Inc." and "NRI" become
**one node**; the lookalike "Northwind Logistics" stays a separate node
because the evidence says it's a different company.
*Look at:* `nodes` in `examples/competitive_intelligence/output/graph.json`
(after running the demo).

## Edge

A relation after assembly — just a fact connecting two things, with an id
(`e012`), qualifiers, timing, and citations. Edge ids are what answers cite.
*Look at:* `edges` in the same graph file.

## Provenance

The receipt trail. Every fact carries the document id and a **verbatim
quote** that supports it, and the kit re-checks the quote against the
document by machine. Provenance survives every stage, which is why a final
strategic conclusion can print the exact sentences it stands on.
*Look at:* any edge's `citations`, or run the demo and read the
"evidence trail" at the end.

## Resolution

Deciding when two mentions are the same real thing. Done by meaning
(descriptions), not by string similarity — and when the evidence is genuinely
unclear (the demo's "Project Helios" could belong to either company), the
kit records the ambiguity instead of guessing.
*Look at:* `examples/competitive_intelligence/fixtures/resolution/entities.json`.

## Multi-hop query

A question no single fact — or single document — answers. "Why did the price
go up, and how does it compare to the competitor?" needs the price change
(doc 1), the stated reason (doc 3), and the competitor's price (doc 4).
The kit plans which entities matter, walks the graph a few hops, and answers
only from what it retrieved, citing each edge.
*Look at:* demo question `q4`, and `test_query.py::test_multi_hop_question_pulls_evidence_across_documents`.

## The graph as shared agent memory

Context windows are temporary; the graph JSON is permanent. Multiple agents
(a pricing analyst, a product analyst, a financial analyst) each query the
**same** graph and a synthesizer combines their cited findings. No agent
passes a giant transcript to another — the graph is the shared world model,
and every agent's claims are checkable against it.
*Look at:* [MULTI_AGENT_PATTERNS.md](MULTI_AGENT_PATTERNS.md) and
`src/kgkit/agents/orchestrator.py`.
