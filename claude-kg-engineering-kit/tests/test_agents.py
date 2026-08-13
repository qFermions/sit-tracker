from kgkit.agents.orchestrator import (
    ANALYST_ROLES,
    run_analyst,
    run_competitive_analysis,
    synthesize,
)
from kgkit.client import MockEngine
from kgkit.models import AnalystFinding, AnalystReport, QueryPlan, SynthesisReport


def test_each_analyst_reports_only_cited_findings(engine, config, store):
    for role in ANALYST_ROLES:
        report, pack, warnings = run_analyst(engine, config, store, role)
        assert report.role == role
        assert report.findings, f"{role} analyst returned nothing"
        allowed = {e.edge_id for e in pack.edges}
        for finding in report.findings:
            assert finding.edge_ids, "finding without citations"
            assert set(finding.edge_ids) <= allowed


def test_full_competitive_analysis_is_evidence_backed(engine, config, store):
    question = "Is the Fleet Pro price increase defensible against Atlas?"
    analysis = run_competitive_analysis(engine, config, store, question)
    assert set(analysis.reports) == set(ANALYST_ROLES)
    synthesis = analysis.synthesis
    assert synthesis is not None and synthesis.key_findings

    # Every synthesis citation must trace into evidence some analyst retrieved.
    union = set()
    for pack in analysis.evidence.values():
        union |= {e.edge_id for e in pack.edges}
    cited = {eid for f in synthesis.key_findings for eid in f.edge_ids}
    assert cited <= union

    # The strategic conclusion must genuinely span sources: the whole reason
    # the graph exists is that no single document contains this answer.
    docs = set()
    for eid in cited:
        for c in store.get_edge(eid).citations:
            docs.add(c.doc_id)
    assert len(docs) >= 4


def test_synthesizer_citations_are_machine_checked(config, store):
    """A synthesis citing an edge outside the analysts' evidence is stripped."""
    engine = MockEngine()
    pricing_pack_plan = QueryPlan(
        entities=["Fleet Pro"], predicates=["changed_price"], max_hops=1, reasoning=""
    )
    engine.add("query_planner", "analyst-pricing", pricing_pack_plan)
    engine.add(
        "analyst",
        "pricing",
        AnalystReport(
            role="pricing",
            question=ANALYST_ROLES["pricing"],
            findings=[AnalystFinding(claim="Price rose to $79.", edge_ids=["e002"])],
        ),
    )
    engine.add(
        "synthesizer",
        "synthesis",
        SynthesisReport(
            assessment="Price rose; and here is an ungrounded flourish.",
            key_findings=[
                AnalystFinding(claim="Price rose.", edge_ids=["e002"]),
                AnalystFinding(claim="Ungrounded.", edge_ids=["e017"]),  # not retrieved
            ],
            confidence="high",
        ),
    )
    report, pack, _ = run_analyst(engine, config, store, "pricing")
    synthesis, warnings = synthesize(
        engine, config, store, "q", {"pricing": report}, {"pricing": pack}
    )
    kept = {eid for f in synthesis.key_findings for eid in f.edge_ids}
    assert kept == {"e002"}
    assert any("e017" in w for w in warnings)


def test_fully_ungrounded_synthesis_is_replaced_not_published(config, store):
    """If no synthesis claim survives citation checking, the prose must not
    survive either (found by the independent review)."""
    engine = MockEngine()
    engine.add(
        "query_planner",
        "analyst-pricing",
        QueryPlan(entities=["Fleet Pro"], predicates=["changed_price"], max_hops=1, reasoning=""),
    )
    engine.add(
        "analyst",
        "pricing",
        AnalystReport(
            role="pricing",
            question=ANALYST_ROLES["pricing"],
            findings=[AnalystFinding(claim="Price rose.", edge_ids=["e002"])],
        ),
    )
    engine.add(
        "synthesizer",
        "synthesis",
        SynthesisReport(
            assessment="FABRICATED: the company will go bankrupt next year.",
            key_findings=[AnalystFinding(claim="Doom.", edge_ids=["e777"])],
            confidence="high",
        ),
    )
    report, pack, _ = run_analyst(engine, config, store, "pricing")
    synthesis, warnings = synthesize(
        engine, config, store, "q", {"pricing": report}, {"pricing": pack}
    )
    assert "FABRICATED" not in synthesis.assessment
    assert synthesis.assessment.startswith("Insufficient evidence")
    assert synthesis.confidence == "low"
    assert synthesis.key_findings == []
    assert any("assessment replaced" in w for w in warnings)
