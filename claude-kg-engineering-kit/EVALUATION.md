# EVALUATION — how to score the system and improve it safely

The eval harness is runnable, not advisory. Metrics are deterministic set
arithmetic against gold data a human wrote; no model grades itself.

## Run it

```bash
kgkit eval run --suite all                 # offline (fixtures)
kgkit eval run --suite all --engine live   # real Claude output
```

Each run writes a record to `evals/runs/<id>.json` containing the suite,
engine, **the exact version + content hash of every prompt used**, the
metrics, and per-case details.

## What is measured, and how

| Suite | Metric | How it's computed |
|---|---|---|
| extraction | `entity_extraction` P/R/F1 | predicted vs gold (doc, normalized surface, type) sets |
| extraction | `relation_extraction` P/R/F1 | predicted vs gold (doc, subject, predicate, object) sets |
| resolution | `resolution_pairs` P/R/F1 | pairwise: every pair of surface forms placed in the same cluster, vs gold clusters |
| resolution | false-merge audit | any `must_not_merge` pair found merged is reported by name |
| qa | `answer_accuracy` | required keywords present (or a correctly refused unanswerable question) |
| qa | `citation_validity` | every cited edge exists in the graph |
| qa | `multihop_pass_rate` | cited edges span ≥ N distinct source documents (N per question) |

**What these checks measure — and can't.** When you run `kgkit eval run`,
answers have already passed the pipeline's own citation stripping, so
`citation_validity` measures "the pipeline emitted a cited answer instead
of refusing" (stripping events appear in the run record's details as
warnings). The keyword check is substring matching — it cannot catch a
negated or mis-attributed answer that still contains the keyword — and the
multi-hop check counts document diversity of citations, not whether each
cited edge supports each sentence. These are honest demo-scale checks;
harden them for your corpus by adding forbidden keywords, more
`expect_insufficient` questions, and human spot-checks of citation trails.

Gold data lives in `evals/gold_*.json` — small, readable, editable. The
shipped gold deliberately contains one relation the demo fixtures miss, so
the offline baseline shows relation recall 0.95, not a fake 1.0: the metric
is demonstrably measuring something.

Two guard-rails against self-deception:

- **Don't tune against one example until it's memorized.** The gold sets
  are your regression floor, not your target. When you improve a prompt,
  add a *new* gold case that captures the failure you fixed — don't reshape
  old cases to fit your output. Keep a couple of gold cases out of your
  iteration loop entirely (a held-out set) and check them only before you
  ship a prompt change.
- **"Looks better" is not a metric.** A change is kept because compared
  runs show it's better, or it's reverted.

## The improvement loop

```bash
# 1. baseline
kgkit eval run --suite extraction --engine live
# 2. inspect the run record's details — extraction runs name every missed
#    and extra entity/relation ("MISSED relation: ...") ; form ONE hypothesis
# 3. edit prompts/extraction.md — and bump its version header:
#    <!-- version: 2 -->
# 4. re-run the SAME suite
kgkit eval run --suite extraction --engine live
# 5. compare
kgkit eval compare evals/runs/<baseline>.json evals/runs/<candidate>.json
```

`compare` prints prompt-version diffs and per-metric deltas
(`P 0.800->0.900 (+0.100)`), so a regression can always be attributed to
the exact prompt change that caused it. Keep the change or revert it;
either way the run records are your history.

## Writing gold data for your own corpus

1. Pick 3–10 documents you know well.
2. List the entities per document (`gold_extraction.json`), the relations
   (`gold_relations.json`), the alias clusters and the merges that must
   NOT happen (`gold_resolution.json`).
3. Write questions with `required_keywords`, `min_distinct_docs` (>1 for
   real multi-hop questions), and at least one `expect_insufficient`
   question the corpus genuinely cannot answer — refusing to hallucinate
   is a behavior worth pinning.
