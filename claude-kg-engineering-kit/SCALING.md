# SCALING — models, cost, and growing graphs

## Model selection

The kit never hard-codes a model. Two environment variables control it:

| Variable | Used for | Default |
|---|---|---|
| `KGKIT_FAST_MODEL` | extraction (high volume, schema-constrained) | `claude-haiku-4-5` |
| `KGKIT_QUALITY_MODEL` | resolution, query planning, answering, analysts, synthesis | `claude-opus-5` |

The principle (which matches Anthropic's own cookbook guidance, SOURCES.md
#1): use a **fast, cheap model where the schema does the heavy lifting**
and your evals prove it's sufficient; use a **stronger model where
conflicting evidence must be weighed** — resolution merges, ambiguous
planning, synthesis. `claude-sonnet-5` is a strong middle option for the
quality tier when cost matters.

Don't take defaults on faith: run `kgkit eval run --engine live` with each
candidate configuration and compare the run records. If Haiku's extraction
F1 matches Sonnet's on *your* corpus, take the cheaper model — that's what
the harness is for. Promises of savings without measurement are marketing.

### Pricing (date-stamped — verify before budgeting)

Anthropic list prices as of **2026-08-13**, from the Claude Docs model
catalog (SOURCES.md #4), per million tokens (input / output):

| Model | Input | Output |
|---|---|---|
| `claude-haiku-4-5` | $1.00 | $5.00 |
| `claude-sonnet-5` | $3.00 / $2.00 intro through 2026-08-31 | $15.00 / $10.00 intro |
| `claude-opus-5` | $5.00 | $25.00 |

Prices change; check https://platform.claude.com/docs/en/pricing before
committing to a budget.

## Cost mechanics that actually matter here

- **Extraction dominates volume.** One call per document, input scales with
  document length. This is why it runs on the fast model.
- **Prompt caching.** Every extraction call shares the same system prompt;
  callers doing large corpora should add `cache_control` so the static
  prompt is cached and you pay mainly for document text. The stage prompts
  are stable files, which is exactly what caching wants.
- **Batch API.** Extraction is embarrassingly parallel and not
  latency-sensitive: Anthropic's Message Batches run at 50% of standard
  price with up-to-24h latency — the natural fit for overnight corpus
  ingestion. (Both features verified against the Claude docs, 2026-08-13;
  neither is wired into this kit's minimal client by default.)
- **Resolution scales with unique entities, not documents.** The kit sends
  one clustering call over aggregated mentions. Past a few hundred unique
  surface forms, block first (group by type, token overlap, or embedding
  neighborhood) and resolve block by block — keep each call under ~100
  candidates.
- **Query cost scales with retrieved evidence, not graph size.** Traversal
  is local (seeds + hops), so a 100k-edge graph and a 19-edge graph cost
  the same to answer a 2-hop question — tune `max_hops` and predicate
  filters before reaching for a bigger model.

## When the JSON file stops being enough

The single-file graph is a feature (openable, diffable, versionable) up to
roughly tens of thousands of edges. Beyond that, the models and validation
logic transfer directly to a real store: nodes/edges map 1:1 onto Neo4j,
Postgres adjacency tables, or similar. Keep the JSON export as the
interchange and audit format — `kgkit validate --docs` re-verifying every
quote is worth keeping no matter where the graph lives.

## Growing and maintaining the graph

Incremental ingestion, superseding vs deleting, conflict handling, prompt
versioning, and periodic integrity checks are covered in
[PIPELINE.md](PIPELINE.md) § Maintenance. The short version: add, don't
overwrite; mark, don't delete; re-validate on a schedule; and never bump a
prompt without an eval run on each side of the change.
