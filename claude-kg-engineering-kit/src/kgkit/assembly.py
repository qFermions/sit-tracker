"""Stage 3 — Assembly: resolved facts → the persistent typed graph.

Assembly is 100% deterministic. The semantic work happened in extraction and
resolution; from here on it is bookkeeping, and bookkeeping is done exactly:
stable ids, normalized predicates, provenance carried through, duplicates
merged by content, and a validation pass at the end.
"""

from __future__ import annotations

from kgkit.graph_store import GraphStore
from kgkit.models import (
    AmbiguousGroup,
    Edge,
    ExtractionResult,
    KnowledgeGraph,
    Node,
    ResolvedEntity,
    SourceDocument,
    SourceRegistryEntry,
    make_node_id,
    normalize_predicate,
    normalize_surface,
    sha256_text,
)


def assemble(
    extractions: dict[str, ExtractionResult],
    entities: list[ResolvedEntity],
    surface_map: dict[str, str],
    docs: list[SourceDocument],
    ambiguous: list[AmbiguousGroup] | None = None,
) -> tuple[GraphStore, list[str]]:
    """Build the graph. Returns (store, warnings)."""
    warnings: list[str] = []
    store = GraphStore(KnowledgeGraph())

    for doc in docs:
        store.graph.sources.append(
            SourceRegistryEntry(
                doc_id=doc.doc_id,
                title=doc.title,
                sha256=sha256_text(doc.text),
                char_count=len(doc.text),
            )
        )

    for entity in entities:
        store.add_node(
            Node(
                node_id=entity.canonical_id,
                name=entity.canonical_name,
                entity_type=entity.entity_type,
                aliases=entity.aliases,
                provenance=entity.provenance,
            )
        )

    surface_map = dict(surface_map)  # local copy; we may extend it

    def node_for_surface(surface: str, doc_id: str) -> str | None:
        node_id = surface_map.get(normalize_surface(surface))
        if node_id:
            return node_id
        # A fact references something never captured as a mention. Create a
        # minimal node rather than silently losing a sourced fact — but say so.
        new_id = make_node_id(surface, "other")
        if store.get_node(new_id) is None:
            store.add_node(
                Node(node_id=new_id, name=surface, entity_type="other")
            )
            warnings.append(
                f"{doc_id}: fact references {surface!r} which had no entity "
                f"mention; created untyped node {new_id}"
            )
        surface_map[normalize_surface(surface)] = new_id
        return new_id

    counter = 0
    for doc_id in sorted(extractions):
        for fact in extractions[doc_id].facts:
            subject_id = node_for_surface(fact.subject, doc_id)
            object_id = None
            if fact.object_entity is not None:
                object_id = node_for_surface(fact.object_entity, doc_id)
            counter += 1
            edge = Edge(
                edge_id=f"e{counter:03d}",
                subject_id=subject_id,
                predicate=normalize_predicate(fact.predicate),
                object_id=object_id,
                object_value=fact.object_value,
                qualifiers=fact.qualifiers,
                time_context=fact.time_context,
                uncertainty=fact.uncertainty,
                confidence=fact.confidence,
                citations=[fact.span],
            )
            store.add_edge(edge)

    if ambiguous:
        store.graph.ambiguous = list(ambiguous)

    issues = store.validate()
    warnings.extend(i for i in issues if i.startswith("WARN:"))
    errors = [i for i in issues if i.startswith("ERROR:")]
    if errors:
        # Graph integrity errors here are pipeline bugs, not model noise.
        raise ValueError("assembled graph failed validation:\n" + "\n".join(errors))
    return store, warnings
