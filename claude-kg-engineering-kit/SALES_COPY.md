# SALES_COPY.md — Gumroad listing draft (for owner review; not published)

## Suggested product title

**Claude Knowledge Graph Engineering Kit — permanent memory for multi-agent
systems**

## One-sentence promise

Turn any folder of text or Markdown documents into a permanent,
citation-backed knowledge graph that your Claude agents share — with every
answer traceable to a verbatim quote in a source document.

## Target buyer

Developers and technically-minded builders using Claude who need agents
that *remember* — competitive-intelligence and research workflows, internal
knowledge bases, due-diligence pipelines — and who are tired of RAG answers
they can't audit. Comfortable with Python basics, or willing to use the
included no-code Claude Projects track.

## The problem it solves

Your agent's knowledge dies with its context window, and similarity
retrieval (classic RAG) answers by finding *paragraphs that look like the
question*. Multi-hop questions don't work that way: "Is the price increase
defensible against the competitor?" has no matching paragraph — the answer
is spread across a pricing page, release notes, an earnings call, and an
analyst note. Embedding search retrieves fragments that resemble the
wording; a knowledge graph instead stores *facts connected to each other*,
so the retrieval step can walk from the product to its price change, to
the stated motive, to the competitor's counter-position — and return each
hop's evidence. Connected facts compose; similar paragraphs don't. (To be
precise: that's an architectural argument, not a benchmark — this kit
ships no RAG head-to-head, and its LIMITATIONS.md says so. For single-fact
lookup questions, plain retrieval is fine — this kit is for when your
questions chain.)

## What's included

- The full Python kit (MIT licensed): 4-stage pipeline — extraction,
  resolution, assembly, multi-hop query — using Claude structured outputs,
  plus a pricing/product/financial analyst team and synthesizer over the
  shared graph.
- Machine-checked honesty: verbatim-quote provenance verified at every
  stage, citations validated in code, "insufficient evidence" instead of
  hallucination, ambiguity preserved instead of guessed.
- A complete runnable demo (fictional competitive-intelligence corpus)
  that works **offline with no API key**, plus 66 offline tests.
- An evaluation harness with real precision/recall/F1, versioned prompt
  records, and run-to-run comparison — so prompt changes are measured, not
  vibed.
- Production prompts, exported JSON schemas, and a no-code **Claude
  Projects** track for non-programmers.
- Documentation written for humans: quickstart, concepts, pipeline,
  multi-agent patterns, evaluation, scaling/cost, limitations, and a
  verified source map.

## Requirements

- Track A: Python 3.10+, `pip`, and an Anthropic API key for live runs
  (the demo and tests run with no key). API usage is billed by Anthropic
  at their rates.
- Track B: a claude.ai plan that includes Projects. No code.

## Honest limitations (also shipped in the product as LIMITATIONS.md)

Single-file JSON graph (comfortable to tens of thousands of edges, not
millions); ingestion reads `.md`/`.txt` (convert PDFs first); facts are
triples + qualifiers; evaluation gold sets are demo-sized examples, not
benchmarks; the kit was built and verified with its offline suite — verify
the live path on your own key with `kgkit demo --engine live` and
`kgkit eval run --engine live`. No performance guarantees.

## Suggested pricing

- **Range:** $39–$79 (comparable dev-tool kits with docs + tests sit here).
- **Launch price:** $39 introductory, raising to $59 after the first cohort
  of feedback.

## FAQ

**Do I need an Anthropic API key?** For live runs on your own documents,
yes (any Claude API key works). The demo, tests, and evaluation harness run
fully offline first, so you can inspect everything before spending a cent.

**Which models does it use?** Configurable by environment variable.
Defaults (verified Aug 2026): Haiku for high-volume extraction, Opus-tier
for judgment stages. Swap freely; the eval harness tells you what your
corpus actually needs.

**Is this a wrapper around a database?** No — the graph is one readable
JSON file with a validator and deterministic traversal. The models map 1:1
onto Neo4j/Postgres when you outgrow the file.

**How is this different from RAG?** See "the problem it solves": it stores
connected facts with provenance instead of retrieving similar text, which
is what makes chained, auditable answers possible.

**Can my non-technical teammate use it?** Track B runs the same method
manually inside a Claude Project, honestly documented (Projects don't run
Python; the instructions say exactly what's manual).

**License?** MIT for the code. The demo corpus is fictional and
redistributable.

**Refunds?** [Owner to set policy.]

## Disclaimer (include verbatim on the listing)

This is an independent product. It is not affiliated with, endorsed by, or
certified by Anthropic. "Claude" is used to describe compatibility with
Anthropic's Claude models and API.

---

*Listing checklist for the owner (not part of the copy): set your name in
LICENSE, set refund policy, attach the ZIP from dist/, price per above. No
testimonials, user counts, or benchmark claims exist — do not add any.
Naming note: the title leads with the "Claude" mark; brand guidelines
usually prefer "X for Claude" phrasing. If you want zero trademark risk on
the marketplace listing, use "Knowledge Graph Engineering Kit for Claude
Multi-Agent Systems" as the display title — the disclaimer below is
required either way.*
