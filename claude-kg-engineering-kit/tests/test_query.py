from kgkit.client import MockEngine
from kgkit.models import Answer, QueryPlan
from kgkit.query import INSUFFICIENT, answer_question, plan_query, retrieve


def test_simple_lookup_cites_the_right_edge(engine, config, store):
    answer, pack, warnings = answer_question(
        engine, config, store, "What does Aurora Dynamics charge for the Atlas platform?", key="q2"
    )
    assert "$59" in answer.answer
    assert answer.cited_edge_ids == ["e012"]
    assert not answer.insufficient_evidence


def test_multi_hop_question_pulls_evidence_across_documents(engine, config, store):
    answer, pack, warnings = answer_question(
        engine,
        config,
        store,
        "Why did Northwind Robotics raise the price of Fleet Pro, and how does "
        "the new price compare with Aurora Dynamics' Atlas?",
        key="q4",
    )
    assert not answer.insufficient_evidence
    docs = set()
    for eid in answer.cited_edge_ids:
        for c in store.get_edge(eid).citations:
            docs.add(c.doc_id)
    # The whole point: no single document contains this answer.
    assert len(docs) >= 3
    # Two-hop retrieval reached the company-level cost-pressure fact.
    assert "e008" in {e.edge_id for e in pack.edges}


def test_unanswerable_question_is_refused(engine, config, store):
    answer, pack, warnings = answer_question(
        engine, config, store, "How many employees does Northwind Robotics have?", key="q3"
    )
    assert answer.insufficient_evidence
    assert answer.cited_edge_ids == []


def test_no_evidence_means_no_model_call(config, store):
    """When traversal finds nothing, the answer stage must never run —
    the model's memory is not allowed to fill the gap."""
    engine = MockEngine()
    engine.add(
        "query_planner",
        "qx",
        QueryPlan(entities=["Zeta Nonexistent Corp"], max_hops=2, reasoning=""),
    )
    # Deliberately NO 'answer' response registered: a call would raise.
    answer, pack, warnings = answer_question(
        engine, config, store, "What does Zeta charge?", key="qx"
    )
    assert answer.insufficient_evidence
    assert answer.answer == INSUFFICIENT
    assert engine.calls == [("query_planner", "qx")]


def test_invalid_citations_are_stripped_not_trusted(config, store):
    engine = MockEngine()
    engine.add(
        "query_planner",
        "qy",
        QueryPlan(entities=["Atlas"], predicates=["priced_at"], max_hops=1, reasoning=""),
    )
    engine.add(
        "answer",
        "qy",
        Answer(
            answer="Atlas costs $59 per month per site.",
            cited_edge_ids=["e012", "e999"],  # one real, one fabricated
        ),
    )
    answer, pack, warnings = answer_question(
        engine, config, store, "Atlas price?", key="qy"
    )
    assert answer.cited_edge_ids == ["e012"]
    assert any("e999" in w for w in warnings)


def test_answer_with_only_fabricated_citations_becomes_insufficient(config, store):
    engine = MockEngine()
    engine.add(
        "query_planner",
        "qz",
        QueryPlan(entities=["Atlas"], predicates=["priced_at"], max_hops=1, reasoning=""),
    )
    engine.add(
        "answer",
        "qz",
        Answer(answer="Something ungrounded.", cited_edge_ids=["e777"]),
    )
    answer, _, _ = answer_question(engine, config, store, "Atlas?", key="qz")
    assert answer.insufficient_evidence


def test_insufficient_answers_never_carry_citations(config, store):
    """A refusal must not look cited: ids attached to an insufficient-evidence
    answer are dropped (found by the independent review)."""
    engine = MockEngine()
    engine.add(
        "query_planner",
        "qi",
        QueryPlan(entities=["Atlas"], predicates=["priced_at"], max_hops=1, reasoning=""),
    )
    engine.add(
        "answer",
        "qi",
        Answer(
            answer="I cannot tell, but here is a made-up flourish.",
            cited_edge_ids=["e999-fabricated"],
            insufficient_evidence=True,
        ),
    )
    answer, _, warnings = answer_question(engine, config, store, "Atlas?", key="qi")
    assert answer.insufficient_evidence
    assert answer.cited_edge_ids == []
    assert any("insufficient-evidence" in w for w in warnings)


def test_plan_hops_are_clamped(config, store):
    engine = MockEngine()
    engine.add(
        "query_planner",
        "qh",
        QueryPlan(entities=["Atlas"], max_hops=99, reasoning=""),
    )
    plan, _ = plan_query(engine, config, store, "anything", key="qh")
    assert plan.max_hops == 4


def test_retrieve_uses_aliases(store):
    plan = QueryPlan(entities=["NRI"], max_hops=1, reasoning="")
    pack = retrieve(store, "q", plan)
    robotics = store.find_nodes("Northwind Robotics")[0]
    assert pack.seed_node_ids == [robotics.node_id]
    assert pack.edges  # the alias reaches the canonical node's edges
