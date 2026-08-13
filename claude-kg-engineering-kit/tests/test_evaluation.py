import json

from kgkit.evaluation import (
    cluster_pairs,
    compare_runs,
    eval_extraction,
    eval_qa,
    eval_resolution,
    prf,
    record_run,
    load_run,
)
from kgkit.models import (
    Answer,
    CandidateFact,
    ExtractionResult,
    MetricResult,
    ResolvedEntity,
    ScalarValue,
    SourceSpan,
)


def test_prf_math_on_known_values():
    m = prf({"a", "b", "c"}, {"b", "c", "d", "e"})
    assert (m.true_positives, m.false_positives, m.false_negatives) == (2, 1, 2)
    assert m.precision == 0.6667 and m.recall == 0.5
    assert m.f1 == 0.5714
    empty = prf(set(), set())
    assert empty.precision == empty.recall == empty.f1 == 0.0


def test_extraction_metrics_catch_misses_and_inventions():
    span = SourceSpan(doc_id="d1", quote="q")
    extractions = {
        "d1": ExtractionResult(
            doc_id="d1",
            facts=[
                CandidateFact(
                    subject="Acme", predicate="priced_at",
                    object_value=ScalarValue(kind="money", text="$5"), span=span,
                ),
                CandidateFact(  # invented: not in gold
                    subject="Acme", predicate="acquired", object_entity="Globex", span=span,
                ),
            ],
        )
    }
    gold_relations = {
        "d1": [
            {"subject": "Acme", "predicate": "priced_at", "object_value_text": "$5"},
            {"subject": "Acme", "predicate": "ships_to", "object_entity": "Mars"},  # missed
        ]
    }
    metrics = eval_extraction(extractions, {"d1": []}, gold_relations)
    rel = metrics["relation_extraction"]
    assert (rel.true_positives, rel.false_positives, rel.false_negatives) == (1, 1, 1)
    assert rel.precision == 0.5 and rel.recall == 0.5


def test_resolution_pairwise_and_false_merge_detection():
    entities = [
        ResolvedEntity(
            canonical_id="company:acme",
            canonical_name="Acme",
            entity_type="company",
            aliases=["ACME International", "Acme Freight"],  # Freight = WRONG merge
        )
    ]
    gold = {
        "clusters": [["Acme", "ACME International"]],
        "must_not_merge": [["Acme", "Acme Freight"]],
    }
    metrics, details = eval_resolution(entities, gold)
    m = metrics["resolution_pairs"]
    assert m.recall == 1.0 and m.precision < 1.0  # extra pairs from the bad merge
    assert any("FALSE MERGE" in d for d in details)


def test_qa_eval_checks_keywords_citations_and_multihop(store):
    gold = [
        {
            "question_id": "g1",
            "question": "?",
            "required_keywords": ["$79"],
            "min_distinct_docs": 2,
        },
        {"question_id": "g2", "question": "?", "expect_insufficient": True},
    ]
    results = [
        {
            "question_id": "g1",
            "answer": Answer(
                answer="It now costs $79.", cited_edge_ids=["e002", "e009"]
            ),
            "evidence": None,
        },
        {
            "question_id": "g2",
            "answer": Answer(answer="No idea.", insufficient_evidence=True),
            "evidence": None,
        },
    ]
    scalars, details = eval_qa(store, results, gold)
    assert scalars["answer_accuracy"] == 1.0
    assert scalars["citation_validity"] == 1.0
    assert scalars["multihop_pass_rate"] == 1.0  # e002 (d1) + e009 (d3) = 2 docs

    # Now break the multihop requirement: citations from a single doc.
    results[0]["answer"] = Answer(answer="It now costs $79.", cited_edge_ids=["e002"])
    scalars, details = eval_qa(store, results, gold)
    assert scalars["multihop_pass_rate"] == 0.0


def test_qa_eval_skips_unknown_question_ids_without_crashing(store):
    gold = [{"question_id": "g1", "question": "?", "required_keywords": ["$79"]}]
    results = [
        {"question_id": "zzz", "answer": Answer(answer="?"), "evidence": None},
        {
            "question_id": "g1",
            "answer": Answer(answer="It costs $79.", cited_edge_ids=["e002"]),
            "evidence": None,
        },
    ]
    scalars, details = eval_qa(store, results, gold)
    assert any("SKIPPED" in d for d in details)
    assert scalars["answer_accuracy"] == 1.0  # denominator excludes the skip


def test_extraction_mismatch_details_name_the_misses():
    from kgkit.evaluation import extraction_mismatch_details

    span = SourceSpan(doc_id="d1", quote="q")
    extractions = {
        "d1": ExtractionResult(
            doc_id="d1",
            facts=[
                CandidateFact(
                    subject="Acme", predicate="acquired", object_entity="Globex",
                    span=span,
                )
            ],
        )
    }
    gold_relations = {
        "d1": [{"subject": "Acme", "predicate": "ships_to", "object_entity": "Mars"}]
    }
    details = extraction_mismatch_details(extractions, {"d1": []}, gold_relations)
    assert any(d.startswith("MISSED relation:") and "ships_to" in d for d in details)
    assert any(d.startswith("EXTRA relation") and "acquired" in d for d in details)


def test_run_records_and_comparison(tmp_path):
    a = record_run(
        tmp_path, "extraction", "fixture",
        {"extraction": "extraction@v1+aaaa"},
        metrics={"relation_extraction": MetricResult(
            precision=0.8, recall=0.7, f1=0.7467, true_positives=7,
            false_positives=2, false_negatives=3)},
    )
    b = record_run(
        tmp_path, "extraction", "fixture",
        {"extraction": "extraction@v2+bbbb"},
        metrics={"relation_extraction": MetricResult(
            precision=0.9, recall=0.8, f1=0.8471, true_positives=8,
            false_positives=1, false_negatives=2)},
    )
    assert load_run(a).suite == "extraction"
    diff = compare_runs(a, b)
    assert "extraction@v1+aaaa -> extraction@v2+bbbb" in diff
    assert "+0.100" in diff  # precision delta is shown
