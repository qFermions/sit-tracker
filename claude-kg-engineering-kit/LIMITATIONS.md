# LIMITATIONS — what this kit does not prove or solve

Honest boundaries, so you can decide what to rely on.

## About the verification you're inheriting

- **The offline suite (66 tests) proves the deterministic machinery**, and
  the fixture demo proves the pipeline end to end — but fixtures are
  recorded stage outputs, not live model calls. The live path uses the
  same code (`client.messages.parse` structured outputs), and it was **not
  smoke-tested during this kit's build** because no API credential was
  available in the build environment. Your first `--engine live` run is
  the first live run on your setup; do it on the demo corpus and diff
  against the fixtures.
- Fixture-mode eval metrics score the *recorded* pipeline. They demonstrate
  that the harness measures correctly (the shipped gold intentionally
  catches a fixture miss at recall 0.95); they say nothing about how any
  live model performs on your corpus until you run `--engine live`.

## Modeling limits

- **Facts are triples with qualifiers.** Genuinely n-ary events ("A sold B
  to C for D in year E") must be decomposed or squeezed into qualifiers.
- **Resolution operates on surface forms corpus-wide.** The same string
  meaning two different things in two documents ("Mercury" the company vs
  the planet) collides unless the surface forms differ. Mitigation, not
  solution: descriptions catch many cases; ambiguity groups catch more;
  a per-document mention-level resolver would be the real fix.
- **Cross-type name collisions** (a product named exactly like a company)
  resolve to one node deterministically with a warning, favoring the first
  type alphabetically. Rename in gold/aliases if this bites your corpus.
- **Quotes are the provenance anchor.** Documents that state facts only
  across multiple non-adjacent sentences may verify poorly quote-by-quote;
  extraction then under-reports rather than fabricating. That trade is
  deliberate.
- **Quote verification proves existence, not support.** The machine check
  confirms a cited quote really appears in the source (with a minimum
  length so trivial fragments don't count) — it does not judge whether the
  quote semantically supports the fact. A live model could in principle
  attach a real-but-irrelevant quote to a wrong fact; spot-check the
  citation trail on corpora that matter, and use the eval harness's gold
  relations to catch systematic drift.
- **Ingestion reads `.md`/`.txt` files.** PDFs, DOCX, and HTML need to be
  converted to text first (any converter works; the pipeline only needs
  plain text with stable content).
- **Predicate filters bound traversal, deliberately.** When a query plan
  lists predicates, edges outside that list are neither returned *nor
  crossed* — an over-narrow plan can make a reachable fact unretrievable
  and produce "insufficient evidence" instead. The planner prompt lists the
  graph's relation types to keep plans complete; leave `predicates` empty
  when in doubt.
- **Temporal reasoning is recorded, not computed.** `time_context` is
  preserved and shown, but the kit does not order events on a timeline or
  reason about intervals.

## Scale and infrastructure limits

- One JSON file, in-memory indexes: comfortable to tens of thousands of
  edges, not millions (see SCALING.md).
- Traversal is BFS with hop/predicate filters — no ranking, no embedding
  similarity, no path scoring. For huge neighborhoods you'll retrieve more
  than you need before the model filters it.
- No concurrency control: two processes writing one graph file will race.
  Wrap writes in your own locking if you parallelize ingestion.
- The resolution stage sends all mentions in one call; very large corpora
  need blocking first (SCALING.md).

## Scope limits

- The evaluation gold sets are small and demo-sized — they demonstrate the
  loop honestly but are not a benchmark, and no benchmark claims are made
  anywhere in this kit.
- The multi-agent layer is sequential orchestration in one process — no
  queues, no retries-across-machines, no parallel execution (the analysts
  are independent and *could* run in parallel; the kit keeps it simple).
- Claude Projects (Track B) is a manual workflow: Projects do not execute
  this kit's Python or call the API on your behalf. The instructions are
  honest about which steps are you copying/pasting and which are Claude
  reasoning.
- This is an independent product. It is not affiliated with, endorsed by,
  or certified by Anthropic, and no performance guarantees are made or
  implied.
