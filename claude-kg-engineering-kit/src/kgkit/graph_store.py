"""Persistent JSON knowledge graph with deterministic traversal.

The graph is a single JSON file a human can open and read. No database, no
framework. Construction, lookup, validation, and traversal are all plain
Python — the model is never used for operations code can perform exactly.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from kgkit.models import (
    Edge,
    KnowledgeGraph,
    Node,
    SourceDocument,
    normalize_surface,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class GraphStore:
    """In-memory wrapper over a :class:`KnowledgeGraph` with indexes."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None):
        self.graph = graph or KnowledgeGraph(created_at=_now_iso())
        self._reindex()

    # -- persistence --------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> "GraphStore":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(KnowledgeGraph.model_validate(data))

    def save(self, path: str | Path) -> None:
        self.graph.updated_at = _now_iso()
        payload = self.graph.model_dump(mode="json")
        Path(path).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # -- indexing -----------------------------------------------------------

    def _reindex(self) -> None:
        self._nodes: dict[str, Node] = {n.node_id: n for n in self.graph.nodes}
        self._edges: dict[str, Edge] = {e.edge_id: e for e in self.graph.edges}
        self._alias_index: dict[str, set[str]] = {}
        for node in self.graph.nodes:
            for name in [node.name, *node.aliases]:
                self._alias_index.setdefault(normalize_surface(name), set()).add(
                    node.node_id
                )

    # -- lookups ------------------------------------------------------------

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        return self._edges.get(edge_id)

    def find_nodes(self, name_or_alias: str) -> list[Node]:
        """Exact (normalized) name/alias lookup. Never fuzzy."""
        ids = self._alias_index.get(normalize_surface(name_or_alias), set())
        return [self._nodes[i] for i in sorted(ids)]

    def edges_for(self, node_id: str) -> list[Edge]:
        return sorted(
            (
                e
                for e in self.graph.edges
                if e.subject_id == node_id or e.object_id == node_id
            ),
            key=lambda e: e.edge_id,
        )

    # -- mutation (deterministic, idempotent) -------------------------------

    def add_node(self, node: Node) -> Node:
        """Insert or merge by node_id. Merging unions aliases and provenance."""
        existing = self._nodes.get(node.node_id)
        if existing is None:
            self.graph.nodes.append(node)
            self._reindex()
            return node
        for alias in [node.name, *node.aliases]:
            if alias != existing.name and alias not in existing.aliases:
                existing.aliases.append(alias)
        seen_attrs = {(a.key, a.value) for a in existing.attributes}
        for attr in node.attributes:
            if (attr.key, attr.value) not in seen_attrs:
                existing.attributes.append(attr)
        seen_spans = {(s.doc_id, s.quote) for s in existing.provenance}
        for span in node.provenance:
            if (span.doc_id, span.quote) not in seen_spans:
                existing.provenance.append(span)
        self._reindex()
        return existing

    @staticmethod
    def edge_fingerprint(edge: Edge) -> tuple:
        if edge.object_value is not None:
            obj = (
                edge.object_value.kind,
                edge.object_value.text,
                edge.object_value.value,
                edge.object_value.unit,
            )
        else:
            obj = (edge.object_id,)
        quals = tuple(sorted((q.key, q.value) for q in edge.qualifiers))
        # status and uncertainty are part of an edge's identity: a retraction
        # or a hedged restatement must never silently merge into an asserted
        # fact. (confidence, a free float, deliberately is not.)
        return (
            edge.subject_id,
            edge.predicate,
            obj,
            edge.time_context,
            quals,
            edge.status,
            edge.uncertainty,
        )

    def add_edge(self, edge: Edge) -> Edge:
        """Insert, deduplicating by content fingerprint (citations union).

        Re-running assembly over the same facts therefore cannot create
        duplicate edges.
        """
        fp = self.edge_fingerprint(edge)
        for existing in self.graph.edges:
            if self.edge_fingerprint(existing) == fp:
                seen = {(s.doc_id, s.quote) for s in existing.citations}
                for span in edge.citations:
                    if (span.doc_id, span.quote) not in seen:
                        existing.citations.append(span)
                return existing
        if edge.edge_id in self._edges:
            raise ValueError(f"duplicate edge_id with different content: {edge.edge_id}")
        self.graph.edges.append(edge)
        self._edges[edge.edge_id] = edge
        return edge

    # -- integrity ----------------------------------------------------------

    def validate(
        self,
        docs: Optional[dict[str, SourceDocument]] = None,
        allowed_relations: Optional[set[str]] = None,
    ) -> list[str]:
        """Return a list of issues. 'ERROR:' items make the graph invalid;
        'WARN:' items are worth a look but not fatal."""
        issues: list[str] = []
        node_ids = [n.node_id for n in self.graph.nodes]
        if len(node_ids) != len(set(node_ids)):
            dupes = sorted({i for i in node_ids if node_ids.count(i) > 1})
            issues.append(f"ERROR: duplicate node ids: {dupes}")
        edge_ids = [e.edge_id for e in self.graph.edges]
        if len(edge_ids) != len(set(edge_ids)):
            dupes = sorted({i for i in edge_ids if edge_ids.count(i) > 1})
            issues.append(f"ERROR: duplicate edge ids: {dupes}")
        known_nodes = set(node_ids)
        known_docs = {s.doc_id for s in self.graph.sources}
        if self.graph.edges and not known_docs:
            issues.append(
                "ERROR: graph has edges but an empty source registry — "
                "citations cannot be checked against known documents"
            )
        if docs is not None:
            from kgkit.provenance import quote_in_doc

            for node in self.graph.nodes:
                for span in node.provenance:
                    if span.doc_id in docs and not quote_in_doc(
                        span.quote, docs[span.doc_id].text
                    ):
                        issues.append(
                            f"ERROR: node {node.node_id} provenance quote not "
                            f"found in {span.doc_id}: {span.quote[:60]!r}"
                        )
        for edge in self.graph.edges:
            eid = edge.edge_id
            if edge.subject_id not in known_nodes:
                issues.append(f"ERROR: edge {eid} has dangling subject {edge.subject_id}")
            if edge.object_id is not None and edge.object_id not in known_nodes:
                issues.append(f"ERROR: edge {eid} has dangling object {edge.object_id}")
            if (edge.object_id is None) == (edge.object_value is None):
                issues.append(
                    f"ERROR: edge {eid} must have exactly one of object_id/object_value"
                )
            if not edge.citations:
                issues.append(f"ERROR: edge {eid} has no citations (provenance required)")
            for span in edge.citations:
                if known_docs and span.doc_id not in known_docs:
                    issues.append(
                        f"ERROR: edge {eid} cites unknown document {span.doc_id}"
                    )
                if docs is not None and span.doc_id in docs:
                    from kgkit.provenance import quote_in_doc

                    if not quote_in_doc(span.quote, docs[span.doc_id].text):
                        issues.append(
                            f"ERROR: edge {eid} citation quote not found in "
                            f"{span.doc_id}: {span.quote[:60]!r}"
                        )
            if allowed_relations is not None and edge.predicate not in allowed_relations:
                issues.append(
                    f"ERROR: edge {eid} uses relation {edge.predicate!r} outside the schema"
                )
            if (
                edge.object_value is not None
                and edge.object_value.kind in ("money", "percent", "number")
                and edge.object_value.value is None
            ):
                issues.append(
                    f"WARN: edge {eid} has a {edge.object_value.kind} value with no "
                    f"parsed number (kept as text: {edge.object_value.text!r})"
                )
        # Same normalized alias on two different nodes is legal (that's what
        # ambiguity preservation looks like) but always worth surfacing.
        for key, ids in sorted(self._alias_index.items()):
            if len(ids) > 1:
                issues.append(
                    f"WARN: name {key!r} maps to multiple nodes: {sorted(ids)}"
                )
        return issues

    # -- deterministic traversal -------------------------------------------

    def traverse(
        self,
        seed_node_ids: Iterable[str],
        max_hops: int = 2,
        predicates: Optional[Iterable[str]] = None,
        include_superseded: bool = False,
    ) -> list[Edge]:
        """Breadth-first edge collection out to ``max_hops`` from the seeds.

        Plain code, fully deterministic: same graph + same seeds = same
        evidence, sorted by edge_id. Retracted edges are never returned;
        superseded edges only on request.
        """
        wanted = set(predicates) if predicates else None
        frontier = {s for s in seed_node_ids if s in self._nodes}
        visited = set(frontier)
        collected: dict[str, Edge] = {}
        for _ in range(max_hops):
            if not frontier:
                break
            next_frontier: set[str] = set()
            for edge in self.graph.edges:
                if edge.status == "retracted":
                    continue
                if edge.status == "superseded" and not include_superseded:
                    continue
                if wanted is not None and edge.predicate not in wanted:
                    continue
                touches = edge.subject_id in frontier or (
                    edge.object_id is not None and edge.object_id in frontier
                )
                if not touches:
                    continue
                collected[edge.edge_id] = edge
                for endpoint in (edge.subject_id, edge.object_id):
                    if endpoint and endpoint not in visited:
                        next_frontier.add(endpoint)
            visited |= next_frontier
            frontier = next_frontier
        return sorted(collected.values(), key=lambda e: e.edge_id)

    # -- rendering (for the answering model and for humans) -----------------

    def render_edge(self, edge: Edge) -> str:
        subj = self._nodes.get(edge.subject_id)
        subj_name = subj.name if subj else edge.subject_id
        if edge.object_id:
            obj_node = self._nodes.get(edge.object_id)
            obj = obj_node.name if obj_node else edge.object_id
        else:
            obj = edge.object_value.text if edge.object_value else "?"
        parts = [f"[{edge.edge_id}] ({subj_name}) --{edge.predicate}--> ({obj})"]
        if edge.qualifiers:
            quals = "; ".join(f"{q.key}={q.value}" for q in edge.qualifiers)
            parts.append(f"{{{quals}}}")
        if edge.time_context:
            parts.append(f"time={edge.time_context}")
        if edge.status != "asserted":
            parts.append(f"status={edge.status}")
        docs = sorted({c.doc_id for c in edge.citations})
        parts.append(f"sources={','.join(docs)}")
        return "  ".join(parts)

    def render_edges(self, edges: Iterable[Edge]) -> str:
        return "\n".join(self.render_edge(e) for e in edges)

    def stats(self) -> dict[str, int]:
        return {
            "nodes": len(self.graph.nodes),
            "edges": len(self.graph.edges),
            "sources": len(self.graph.sources),
            "ambiguous_groups": len(self.graph.ambiguous),
        }
