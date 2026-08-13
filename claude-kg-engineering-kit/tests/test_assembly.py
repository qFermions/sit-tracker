from kgkit.assembly import assemble
from kgkit.models import (
    CandidateFact,
    EntityMention,
    ExtractionResult,
    ResolvedEntity,
    ScalarValue,
    SourceDocument,
    SourceSpan,
)


def test_demo_graph_shape(store):
    stats = store.stats()
    assert stats == {
        "nodes": 10,
        "edges": 19,
        "sources": 6,
        "ambiguous_groups": 1,
    }


def test_alias_subject_lands_on_canonical_node(store):
    """The d5 fact was written with subject 'NRI'; assembly must attach it to
    the resolved Northwind Robotics node, not a duplicate."""
    robotics = store.find_nodes("Northwind Robotics")[0]
    strategy_edges = [
        e for e in store.graph.edges if e.predicate == "pursues_strategy"
    ]
    assert len(strategy_edges) == 1
    assert strategy_edges[0].subject_id == robotics.node_id


def test_every_edge_keeps_its_citation(store):
    assert all(e.citations for e in store.graph.edges)


def test_source_registry_is_complete(store, docs):
    assert {s.doc_id for s in store.graph.sources} == {d.doc_id for d in docs}
    assert all(s.sha256 and s.char_count > 0 for s in store.graph.sources)


def test_assembled_graph_validates_against_source_docs(store, docs_by_id):
    issues = store.validate(docs=docs_by_id)
    errors = [i for i in issues if i.startswith("ERROR:")]
    assert errors == []


def test_unmentioned_fact_object_creates_flagged_node():
    doc = SourceDocument(doc_id="d1", title="t", text="Acme acquired Globex today.")
    extraction = ExtractionResult(
        doc_id="d1",
        mentions=[
            EntityMention(
                surface_form="Acme",
                entity_type="company",
                description="acquirer",
                span=SourceSpan(doc_id="d1", quote="Acme acquired Globex"),
            )
        ],
        facts=[
            CandidateFact(
                subject="Acme",
                predicate="acquired",
                object_entity="Globex",  # never mentioned as an entity
                span=SourceSpan(doc_id="d1", quote="Acme acquired Globex today"),
            )
        ],
    )
    entities = [
        ResolvedEntity(
            canonical_id="company:acme", canonical_name="Acme", entity_type="company"
        )
    ]
    store, warnings = assemble(
        {"d1": extraction}, entities, {"acme": "company:acme"}, [doc]
    )
    assert store.get_node("other:globex") is not None
    assert any("had no entity mention" in w for w in warnings)


def test_reassembly_is_idempotent_no_duplicate_edges():
    doc = SourceDocument(doc_id="d1", title="t", text="Acme costs $5 per month.")
    fact = CandidateFact(
        subject="Acme",
        predicate="priced_at",
        object_value=ScalarValue(kind="money", text="$5 per month", value=5),
        span=SourceSpan(doc_id="d1", quote="Acme costs $5 per month"),
    )
    extraction = ExtractionResult(
        doc_id="d1",
        mentions=[
            EntityMention(
                surface_form="Acme",
                entity_type="company",
                description="vendor",
                span=SourceSpan(doc_id="d1", quote="Acme costs $5"),
            )
        ],
        facts=[fact, fact.model_copy(deep=True)],  # same fact extracted twice
    )
    entities = [
        ResolvedEntity(
            canonical_id="company:acme", canonical_name="Acme", entity_type="company"
        )
    ]
    store, _ = assemble({"d1": extraction}, entities, {"acme": "company:acme"}, [doc])
    assert len(store.graph.edges) == 1  # deduplicated by content fingerprint
