import pytest
from pydantic import ValidationError

from kgkit.models import (
    Edge,
    KnowledgeGraph,
    Node,
    ScalarValue,
    SourceSpan,
    make_node_id,
    normalize_predicate,
    normalize_surface,
    slugify,
)


def test_unknown_fields_rejected_everywhere():
    with pytest.raises(ValidationError):
        Node(node_id="x", name="X", entity_type="company", bogus_field=1)
    with pytest.raises(ValidationError):
        SourceSpan(doc_id="d", quote="q", offset=3)


def test_entity_type_is_a_closed_set():
    with pytest.raises(ValidationError):
        Node(node_id="x", name="X", entity_type="galaxy")


def test_scalar_value_kinds():
    v = ScalarValue(kind="money", text="$79 per month", value=79, unit="USD/month")
    assert v.value == 79
    with pytest.raises(ValidationError):
        ScalarValue(kind="price", text="x")
    # Unknown stays None — absence is not zero.
    assert ScalarValue(kind="percent", text="high").value is None


def test_slug_and_ids_are_stable():
    assert slugify("Acme Corp.") == "acme-corp"
    assert make_node_id("Aurora Dynamics", "company") == "company:aurora-dynamics"
    assert normalize_predicate("Changed Price!") == "changed_price"


def test_normalize_surface_strips_corporate_suffixes_but_keeps_identity():
    assert normalize_surface("Northwind Robotics, Inc.") == normalize_surface(
        "Northwind Robotics"
    )
    # Lookalike companies stay distinct after normalization.
    assert normalize_surface("Northwind Robotics") != normalize_surface(
        "Northwind Logistics"
    )


def test_graph_roundtrip_via_json():
    g = KnowledgeGraph(
        nodes=[Node(node_id="company:a", name="A", entity_type="company")],
        edges=[
            Edge(
                edge_id="e1",
                subject_id="company:a",
                predicate="priced_at",
                object_value=ScalarValue(kind="money", text="$1", value=1),
                citations=[SourceSpan(doc_id="d1", quote="costs $1")],
            )
        ],
    )
    restored = KnowledgeGraph.model_validate(g.model_dump(mode="json"))
    assert restored == g
