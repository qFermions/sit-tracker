from kgkit.client import MockEngine
from kgkit.config import KitConfig
from kgkit.models import (
    EntityMention,
    ExtractionResult,
    SourceSpan,
)
from kgkit.resolution import MentionIndex, resolve


def mention(surface, etype, desc, doc):
    return EntityMention(
        surface_form=surface,
        entity_type=etype,
        description=desc,
        span=SourceSpan(doc_id=doc, quote=f"...{surface}..."),
    )


def extractions():
    return {
        "d1": ExtractionResult(
            doc_id="d1",
            mentions=[
                mention("Acme Corp.", "company", "widget maker", "d1"),
                mention("Acme Freight", "company", "unrelated trucking firm", "d1"),
            ],
        ),
        "d2": ExtractionResult(
            doc_id="d2",
            mentions=[
                mention("Acme", "company", "the widget maker again", "d2"),
                mention("Helios", "other", "initiative of unclear ownership", "d2"),
            ],
        ),
    }


def test_mention_index_aggregates_deterministically():
    index = MentionIndex(extractions())
    assert index.surface_forms() == ["Acme", "Acme Corp.", "Acme Freight", "Helios"]
    rendered = index.render()
    assert 'type="company"' in rendered and "unrelated trucking firm" in rendered


def make_engine(clusters, ambiguous=None):
    engine = MockEngine()
    engine.add(
        "resolution",
        "entities",
        {"clusters": clusters, "ambiguous": ambiguous or []},
    )
    return engine


def test_supported_merge_creates_one_node_with_aliases():
    engine = make_engine(
        [
            {
                "canonical_name": "Acme Corp.",
                "entity_type": "company",
                "members": ["Acme Corp.", "Acme"],
                "rationale": "described as the same widget maker",
            }
        ]
    )
    entities, surface_map, _, warnings = resolve(engine, KitConfig(), extractions())
    acme = next(e for e in entities if e.canonical_name == "Acme Corp.")
    assert acme.decision == "merged"
    assert acme.aliases == ["Acme"]
    # The lookalike was never claimed, so it stays its own entity.
    freight = next(e for e in entities if e.canonical_name == "Acme Freight")
    assert freight.decision == "single"
    assert surface_map["acme freight"] != surface_map["acme"]


def test_model_cannot_invent_or_double_assign_members():
    engine = make_engine(
        [
            {
                "canonical_name": "Acme",
                "entity_type": "company",
                "members": ["Acme", "Acme Corp.", "Globex"],  # Globex was never extracted
                "rationale": "x",
            }
        ]
    )
    entities, surface_map, _, warnings = resolve(engine, KitConfig(), extractions())
    assert any("invents surface form" in w for w in warnings)
    assert "globex" not in surface_map  # invented member dropped, not trusted


def test_ambiguity_is_preserved_not_forced():
    engine = make_engine(
        [],
        ambiguous=[
            {
                "surface_forms": ["Helios"],
                "reason": "could belong to either company",
            }
        ],
    )
    entities, surface_map, result, _ = resolve(engine, KitConfig(), extractions())
    helios = next(e for e in entities if e.canonical_name == "Helios")
    assert helios.decision == "ambiguous"
    assert result.ambiguous and result.ambiguous[0].surface_forms == ["Helios"]


def test_demo_false_merge_guard(store):
    """The lookalike trucking broker must be a distinct node in the demo graph."""
    robotics = store.find_nodes("Northwind Robotics")
    logistics = store.find_nodes("Northwind Logistics")
    assert len(robotics) == 1 and len(logistics) == 1
    assert robotics[0].node_id != logistics[0].node_id
    # And the alias really merged: NRI resolves to the robotics node.
    assert store.find_nodes("NRI")[0].node_id == robotics[0].node_id


def test_demo_ambiguity_recorded_on_graph(store):
    names = [g.surface_forms for g in store.graph.ambiguous]
    assert ["Project Helios"] in names
    helios = store.find_nodes("Project Helios")
    assert len(helios) == 1  # kept as its own node, merged into nothing
