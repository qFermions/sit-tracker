"""Evaluation: real precision/recall/F1, recorded runs, comparable versions.

Nothing here asks a model to grade itself. Metrics are deterministic set
arithmetic against gold data a human wrote, run records capture the exact
prompt versions used, and two runs can be diffed metric by metric.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from kgkit.graph_store import GraphStore
from kgkit.models import (
    Answer,
    EvalRunRecord,
    EvidencePack,
    ExtractionResult,
    MetricResult,
    ResolvedEntity,
    normalize_predicate,
    normalize_surface,
)


# ---------------------------------------------------------------------------
# Metric arithmetic
# ---------------------------------------------------------------------------


def prf(predicted: set, gold: set) -> MetricResult:
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return MetricResult(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )


def _norm_value_text(text: str) -> str:
    return " ".join(text.lower().replace(",", "").split())


# ---------------------------------------------------------------------------
# Extraction evaluation
# ---------------------------------------------------------------------------


def entity_keys(extractions: dict[str, ExtractionResult]) -> set:
    keys = set()
    for doc_id, result in extractions.items():
        for m in result.mentions:
            keys.add((doc_id, normalize_surface(m.surface_form), m.entity_type))
    return keys


def gold_entity_keys(gold: dict) -> set:
    keys = set()
    for doc_id, items in gold.items():
        for item in items:
            keys.add((doc_id, normalize_surface(item["surface"]), item["type"]))
    return keys


def fact_keys(extractions: dict[str, ExtractionResult]) -> set:
    keys = set()
    for doc_id, result in extractions.items():
        for f in result.facts:
            if f.object_entity is not None:
                obj = ("entity", normalize_surface(f.object_entity))
            else:
                obj = ("value", _norm_value_text(f.object_value.text))
            keys.add(
                (
                    doc_id,
                    normalize_surface(f.subject),
                    normalize_predicate(f.predicate),
                    obj,
                )
            )
    return keys


def gold_fact_keys(gold: dict) -> set:
    keys = set()
    for doc_id, items in gold.items():
        for item in items:
            if "object_entity" in item:
                obj = ("entity", normalize_surface(item["object_entity"]))
            else:
                obj = ("value", _norm_value_text(item["object_value_text"]))
            keys.add(
                (
                    doc_id,
                    normalize_surface(item["subject"]),
                    normalize_predicate(item["predicate"]),
                    obj,
                )
            )
    return keys


def eval_extraction(
    extractions: dict[str, ExtractionResult],
    gold_entities: dict,
    gold_relations: dict,
) -> dict[str, MetricResult]:
    return {
        "entity_extraction": prf(entity_keys(extractions), gold_entity_keys(gold_entities)),
        "relation_extraction": prf(fact_keys(extractions), gold_fact_keys(gold_relations)),
    }


def extraction_mismatch_details(
    extractions: dict[str, ExtractionResult],
    gold_entities: dict,
    gold_relations: dict,
) -> list[str]:
    """Name every miss and invention, so 'inspect the run record' works.

    A run record that only says false_negatives=1 can't drive the improvement
    loop; this says WHICH fact was missed."""
    details: list[str] = []
    pred_e, gold_e = entity_keys(extractions), gold_entity_keys(gold_entities)
    pred_f, gold_f = fact_keys(extractions), gold_fact_keys(gold_relations)
    for key in sorted(gold_e - pred_e):
        details.append(f"MISSED entity: {key}")
    for key in sorted(pred_e - gold_e):
        details.append(f"EXTRA entity (not in gold): {key}")
    for key in sorted(gold_f - pred_f):
        details.append(f"MISSED relation: {key}")
    for key in sorted(pred_f - gold_f):
        details.append(f"EXTRA relation (not in gold): {key}")
    return details


# ---------------------------------------------------------------------------
# Resolution evaluation (pairwise clustering metric + false-merge audit)
# ---------------------------------------------------------------------------


def cluster_pairs(clusters: list[list[str]]) -> set[frozenset]:
    pairs = set()
    for cluster in clusters:
        names = sorted({normalize_surface(s) for s in cluster})
        for a, b in combinations(names, 2):
            pairs.add(frozenset((a, b)))
    return pairs


def predicted_clusters(entities: list[ResolvedEntity]) -> list[list[str]]:
    return [[e.canonical_name, *e.aliases] for e in entities]


def eval_resolution(
    entities: list[ResolvedEntity], gold: dict
) -> tuple[dict[str, MetricResult], list[str]]:
    predicted = cluster_pairs(predicted_clusters(entities))
    gold_pairs = cluster_pairs(gold["clusters"])
    details = []
    for pair in gold.get("must_not_merge", []):
        key = frozenset(normalize_surface(s) for s in pair)
        if key in predicted:
            details.append(f"FALSE MERGE: {pair} were merged but must stay distinct")
    return {"resolution_pairs": prf(predicted, gold_pairs)}, details


# ---------------------------------------------------------------------------
# Multi-hop QA + citation evaluation
# ---------------------------------------------------------------------------


def eval_qa(
    store: GraphStore,
    results: list[dict],  # {"question_id", "answer": Answer, "evidence": EvidencePack}
    gold: list[dict],
) -> tuple[dict[str, float], list[str]]:
    gold_by_id = {g["question_id"]: g for g in gold}
    evaluated = 0
    answered_correct = 0
    citations_valid = 0
    citations_total_qs = 0
    multihop_pass = 0
    multihop_total = 0
    details: list[str] = []

    for item in results:
        qid = item["question_id"]
        answer: Answer = item["answer"]
        g = gold_by_id.get(qid)
        if g is None:
            details.append(f"{qid}: SKIPPED — no gold entry with this question_id")
            continue
        evaluated += 1

        if g.get("expect_insufficient"):
            ok = answer.insufficient_evidence
            details.append(
                f"{qid}: expected insufficient-evidence -> "
                + ("PASS" if ok else f"FAIL (answered: {answer.answer[:80]!r})")
            )
            if ok:
                answered_correct += 1
            continue

        text = answer.answer.lower()
        missing = [k for k in g["required_keywords"] if k.lower() not in text]
        keyword_ok = not missing and not answer.insufficient_evidence
        if keyword_ok:
            answered_correct += 1
        details.append(
            f"{qid}: answer keywords -> "
            + ("PASS" if keyword_ok else f"FAIL (missing: {missing})")
        )

        citations_total_qs += 1
        cited = answer.cited_edge_ids
        edges = [store.get_edge(eid) for eid in cited]
        all_exist = bool(cited) and all(e is not None for e in edges)
        if all_exist:
            citations_valid += 1
        details.append(
            f"{qid}: citations exist -> " + ("PASS" if all_exist else f"FAIL ({cited})")
        )

        min_docs = g.get("min_distinct_docs", 1)
        if min_docs > 1:
            multihop_total += 1
            docs = set()
            for e in edges:
                if e is not None:
                    docs.update(c.doc_id for c in e.citations)
            ok = len(docs) >= min_docs
            if ok:
                multihop_pass += 1
            details.append(
                f"{qid}: multi-hop (needs facts from >={min_docs} docs, got "
                f"{len(docs)}) -> " + ("PASS" if ok else "FAIL")
            )

    n = evaluated
    metrics = {
        "answer_accuracy": round(answered_correct / n, 4) if n else 0.0,
        "citation_validity": (
            round(citations_valid / citations_total_qs, 4) if citations_total_qs else 0.0
        ),
        "multihop_pass_rate": (
            round(multihop_pass / multihop_total, 4) if multihop_total else 0.0
        ),
    }
    return metrics, details


# ---------------------------------------------------------------------------
# Run records and comparison
# ---------------------------------------------------------------------------


def record_run(
    runs_dir: str | Path,
    suite: str,
    engine_name: str,
    prompt_versions: dict[str, str],
    metrics: dict[str, MetricResult] | None = None,
    scalar_metrics: dict[str, float] | None = None,
    details: list[str] | None = None,
) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_id = f"{timestamp}-{suite}-{engine_name}"
    # Guard against id collisions (e.g. two runs in the same microsecond tick).
    n = 2
    while (Path(runs_dir) / f"{run_id}.json").exists():
        run_id = f"{timestamp}-{suite}-{engine_name}-{n}"
        n += 1
    record = EvalRunRecord(
        run_id=run_id,
        timestamp=timestamp,
        suite=suite,
        engine=engine_name,
        prompt_versions=prompt_versions,
        metrics=metrics or {},
        scalar_metrics=scalar_metrics or {},
        details=details or [],
    )
    runs_path = Path(runs_dir)
    runs_path.mkdir(parents=True, exist_ok=True)
    out = runs_path / f"{run_id}.json"
    out.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8"
    )
    return out


def load_run(path: str | Path) -> EvalRunRecord:
    return EvalRunRecord.model_validate(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def compare_runs(path_a: str | Path, path_b: str | Path) -> str:
    """Metric-by-metric diff of two recorded runs, prompt versions included."""
    a, b = load_run(path_a), load_run(path_b)
    lines = [
        f"A: {a.run_id}  (suite={a.suite}, engine={a.engine})",
        f"B: {b.run_id}  (suite={b.suite}, engine={b.engine})",
        "",
    ]
    changed = {
        name
        for name in set(a.prompt_versions) | set(b.prompt_versions)
        if a.prompt_versions.get(name) != b.prompt_versions.get(name)
    }
    if changed:
        lines.append("Prompt versions that differ:")
        for name in sorted(changed):
            lines.append(
                f"  {name}: {a.prompt_versions.get(name, '-')} -> "
                f"{b.prompt_versions.get(name, '-')}"
            )
    else:
        lines.append("Prompt versions: identical")
    lines.append("")

    for name in sorted(set(a.metrics) | set(b.metrics)):
        ma, mb = a.metrics.get(name), b.metrics.get(name)
        if ma and mb:
            lines.append(
                f"{name}: P {ma.precision:.3f}->{mb.precision:.3f} "
                f"({mb.precision - ma.precision:+.3f})  "
                f"R {ma.recall:.3f}->{mb.recall:.3f} "
                f"({mb.recall - ma.recall:+.3f})  "
                f"F1 {ma.f1:.3f}->{mb.f1:.3f} ({mb.f1 - ma.f1:+.3f})"
            )
        else:
            lines.append(f"{name}: only in {'A' if ma else 'B'}")
    for name in sorted(set(a.scalar_metrics) | set(b.scalar_metrics)):
        va, vb = a.scalar_metrics.get(name), b.scalar_metrics.get(name)
        if va is not None and vb is not None:
            lines.append(f"{name}: {va:.3f} -> {vb:.3f} ({vb - va:+.3f})")
        else:
            lines.append(f"{name}: only in {'A' if va is not None else 'B'}")
    return "\n".join(lines)
