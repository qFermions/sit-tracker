import pytest

from kgkit.graph_store import GraphStore
from kgkit.models import Edge, KnowledgeGraph, Node, ScalarValue, SourceSpan


def span(doc="d1", quote="quoted text"):
    return SourceSpan(doc_id=doc, quote=quote)


def node(nid, name=None, etype="company"):
    return Node(node_id=nid, name=name or nid, entity_type=etype)


def edge(eid, subj, pred, obj=None, value=None, status="asserted"):
    return Edge(
        edge_id=eid,
        subject_id=subj,
        predicate=pred,
        object_id=obj,
        object_value=value,
        status=status,
        citations=[span()],
    )


@pytest.fixture
def small_store():
    s = GraphStore(KnowledgeGraph())
    for n in ["company:a", "company:b", "company:c", "company:d"]:
        s.add_node(node(n))
    # a -> b -> c -> d chain plus a scalar edge on a
    s.add_edge(edge("e1", "company:a", "partners_with", obj="company:b"))
    s.add_edge(edge("e2", "company:b", "supplies", obj="company:c"))
    s.add_edge(edge("e3", "company:c", "owns", obj="company:d"))
    s.add_edge(
        edge(
            "e4",
            "company:a",
            "priced_at",
            value=ScalarValue(kind="money", text="$5", value=5),
        )
    )
    return s


def test_save_load_roundtrip(tmp_path, small_store):
    path = tmp_path / "graph.json"
    small_store.save(path)
    loaded = GraphStore.load(path)
    assert loaded.graph.nodes == small_store.graph.nodes
    assert loaded.graph.edges == small_store.graph.edges


def test_add_node_merges_aliases_and_provenance(small_store):
    merged = small_store.add_node(
        Node(
            node_id="company:a",
            name="A Corp",
            entity_type="company",
            aliases=["The A"],
            provenance=[span("d9", "a corp exists")],
        )
    )
    assert "A Corp" in merged.aliases and "The A" in merged.aliases
    assert any(p.doc_id == "d9" for p in merged.provenance)
    assert small_store.find_nodes("The A")[0].node_id == "company:a"


def test_add_edge_dedupes_by_content_and_unions_citations(small_store):
    duplicate = edge("e99", "company:a", "partners_with", obj="company:b")
    duplicate.citations = [span("d2", "another quote")]
    result = small_store.add_edge(duplicate)
    assert result.edge_id == "e1"  # merged into the existing edge
    assert len([e for e in small_store.graph.edges if e.predicate == "partners_with"]) == 1
    assert {c.doc_id for c in result.citations} == {"d1", "d2"}


def test_validate_catches_integrity_errors():
    s = GraphStore(KnowledgeGraph())
    s.add_node(node("company:a"))
    s.graph.edges.append(edge("e1", "company:a", "owns", obj="company:ghost"))
    s.graph.edges.append(
        Edge(edge_id="e2", subject_id="company:a", predicate="broken", citations=[span()])
    )  # neither object_id nor object_value
    s.graph.edges.append(
        Edge(
            edge_id="e3",
            subject_id="company:a",
            predicate="uncited",
            object_id="company:a",
            citations=[],
        )
    )
    issues = "\n".join(s.validate())
    assert "dangling object company:ghost" in issues
    assert "exactly one of object_id/object_value" in issues
    assert "no citations" in issues


def test_conflicting_status_or_uncertainty_never_silently_merges(small_store):
    """A retraction or hedged restatement of a fact is a distinct edge, not a
    dedupe target (found by the independent review)."""
    retraction = edge("e50", "company:a", "partners_with", obj="company:b",
                      status="retracted")
    kept = small_store.add_edge(retraction)
    assert kept.edge_id == "e50"  # NOT merged into asserted e1
    hedged = edge("e51", "company:a", "partners_with", obj="company:b")
    hedged.uncertainty = "uncertain"
    kept2 = small_store.add_edge(hedged)
    assert kept2.edge_id == "e51"
    # And differing parsed values don't merge just because text matches:
    v1 = edge("e52", "company:a", "priced_at",
              value=ScalarValue(kind="money", text="$5", value=500.0, unit="EUR"))
    kept3 = small_store.add_edge(v1)
    assert kept3.edge_id == "e52"  # existing e4 has value=5, no unit


def test_edges_with_empty_source_registry_is_an_error(small_store):
    assert small_store.graph.sources == []
    issues = small_store.validate()
    assert any("empty source registry" in i for i in issues if i.startswith("ERROR:"))


def test_validate_relation_whitelist(small_store):
    issues = small_store.validate(allowed_relations={"partners_with", "priced_at"})
    errors = [i for i in issues if i.startswith("ERROR:")]
    assert any("supplies" in e for e in errors)
    assert any("owns" in e for e in errors)


def test_traversal_hop_semantics(small_store):
    one_hop = {e.edge_id for e in small_store.traverse(["company:a"], max_hops=1)}
    assert one_hop == {"e1", "e4"}
    two_hop = {e.edge_id for e in small_store.traverse(["company:a"], max_hops=2)}
    assert two_hop == {"e1", "e2", "e4"}
    three_hop = {e.edge_id for e in small_store.traverse(["company:a"], max_hops=3)}
    assert three_hop == {"e1", "e2", "e3", "e4"}


def test_traversal_predicate_filter(small_store):
    only = small_store.traverse(["company:a"], max_hops=3, predicates=["partners_with"])
    assert {e.edge_id for e in only} == {"e1"}


def test_traversal_excludes_retracted_and_superseded(small_store):
    small_store.add_edge(
        edge("e5", "company:a", "acquired", obj="company:c", status="retracted")
    )
    small_store.add_edge(
        edge("e6", "company:a", "leased", obj="company:c", status="superseded")
    )
    ids = {e.edge_id for e in small_store.traverse(["company:a"], max_hops=1)}
    assert "e5" not in ids and "e6" not in ids
    with_super = {
        e.edge_id
        for e in small_store.traverse(["company:a"], max_hops=1, include_superseded=True)
    }
    assert "e6" in with_super and "e5" not in with_super


def test_traversal_is_deterministic(small_store):
    a = [e.edge_id for e in small_store.traverse(["company:a"], max_hops=3)]
    b = [e.edge_id for e in small_store.traverse(["company:a"], max_hops=3)]
    assert a == b == sorted(a)
