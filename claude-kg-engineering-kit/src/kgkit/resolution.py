"""Stage 2 — Resolution: which mentions are the same real-world entity?

Deterministic code does what code can do safely: collecting mentions,
grouping exactly-identical surface forms, indexing descriptions. Claude is
used only for the judgment call — clustering different surface forms by
meaning — and its output is validated: it may only cluster surface forms it
was actually given, each surface form lands in at most one cluster, and
anything it leaves out stays a separate entity.

Two safety properties, both enforced and tested:

- **No merge without evidence.** String similarity alone never merges; the
  prompt and the tests treat lookalike names ("Northwind Robotics" vs
  "Northwind Logistics") as distinct unless the descriptions support a merge.
- **Ambiguity survives.** Surface forms the model marks ambiguous stay
  separate nodes and are recorded on the graph, not forced into a cluster.
"""

from __future__ import annotations

from collections import defaultdict

from kgkit.client import Engine, run_with_repair
from kgkit.config import KitConfig
from kgkit.models import (
    ExtractionResult,
    ResolutionResult,
    ResolvedEntity,
    SourceSpan,
    make_node_id,
    normalize_surface,
)
from kgkit.prompts import load_prompt

STAGE = "resolution"


class MentionIndex:
    """Deterministic aggregation of mentions across extraction results."""

    def __init__(self, extractions: dict[str, ExtractionResult]):
        # (surface_form, entity_type) -> {"descriptions": [...], "docs": [...], "spans": [...]}
        self.entries: dict[tuple[str, str], dict] = {}
        for doc_id in sorted(extractions):
            for mention in extractions[doc_id].mentions:
                key = (mention.surface_form, mention.entity_type)
                entry = self.entries.setdefault(
                    key, {"descriptions": [], "docs": [], "spans": []}
                )
                if mention.description not in entry["descriptions"]:
                    entry["descriptions"].append(mention.description)
                if doc_id not in entry["docs"]:
                    entry["docs"].append(doc_id)
                entry["spans"].append(mention.span)

    def surface_forms(self) -> list[str]:
        return sorted({surface for surface, _ in self.entries})

    def types_of(self, surface: str) -> set[str]:
        return {t for s, t in self.entries if s == surface}

    def render(self) -> str:
        by_type: dict[str, list[str]] = defaultdict(list)
        for (surface, etype), entry in sorted(self.entries.items()):
            descs = "; ".join(entry["descriptions"])
            docs = ", ".join(entry["docs"])
            by_type[etype].append(f'- "{surface}" (in {docs}): {descs}')
        blocks = []
        for etype in sorted(by_type):
            body = "\n".join(by_type[etype])
            blocks.append(f'<entities type="{etype}">\n{body}\n</entities>')
        return "\n\n".join(blocks)


def _validate_resolution(result: ResolutionResult, index: MentionIndex) -> list[str]:
    issues: list[str] = []
    known = set(index.surface_forms())
    assigned: dict[str, str] = {}
    for cluster in result.clusters:
        if not cluster.members:
            issues.append(f"cluster {cluster.canonical_name!r} has no members")
        for member in cluster.members:
            if member not in known:
                issues.append(
                    f"cluster {cluster.canonical_name!r} invents surface form "
                    f"{member!r} that was never extracted"
                )
                continue
            if member in assigned:
                issues.append(
                    f"surface form {member!r} assigned to two clusters "
                    f"({assigned[member]!r} and {cluster.canonical_name!r})"
                )
            assigned[member] = cluster.canonical_name
            if cluster.entity_type not in index.types_of(member):
                issues.append(
                    f"cluster {cluster.canonical_name!r} has type "
                    f"{cluster.entity_type} but member {member!r} was extracted "
                    f"with type(s) {sorted(index.types_of(member))}"
                )
    for group in result.ambiguous:
        for member in group.surface_forms:
            if member not in known:
                issues.append(f"ambiguous group invents surface form {member!r}")
            if member in assigned:
                issues.append(
                    f"surface form {member!r} is both clustered and ambiguous"
                )
    return issues


def resolve(
    engine: Engine,
    config: KitConfig,
    extractions: dict[str, ExtractionResult],
) -> tuple[list[ResolvedEntity], dict[str, str], ResolutionResult, list[str]]:
    """Returns (resolved entities, surface→node_id map, raw result, warnings)."""
    prompt = load_prompt("resolution")
    index = MentionIndex(extractions)
    if not index.entries:
        return [], {}, ResolutionResult(), ["no mentions to resolve"]

    result, issues = run_with_repair(
        engine,
        stage=STAGE,
        system_prompt=prompt.text,
        user_input=index.render(),
        response_model=ResolutionResult,
        key="entities",
        validator=lambda r: _validate_resolution(r, index),
        max_attempts=config.max_repair_attempts,
    )
    warnings = [f"resolution: {i}" for i in issues]

    # Deterministic post-processing. Drop invalid members instead of trusting them.
    known = set(index.surface_forms())
    used_ids: set[str] = set()
    entities: list[ResolvedEntity] = []
    surface_map: dict[str, str] = {}
    claimed: set[str] = set()

    def unique_id(name: str, etype: str) -> str:
        base = make_node_id(name, etype)
        node_id, n = base, 2
        while node_id in used_ids:
            node_id = f"{base}-{n}"
            n += 1
        used_ids.add(node_id)
        return node_id

    def spans_for(surfaces: list[str]) -> list[SourceSpan]:
        spans: list[SourceSpan] = []
        seen = set()
        for surface in surfaces:
            for etype in sorted(index.types_of(surface)):
                for span in index.entries[(surface, etype)]["spans"]:
                    key = (span.doc_id, span.quote)
                    if key not in seen:
                        seen.add(key)
                        spans.append(span)
        return spans

    for cluster in result.clusters:
        members = [m for m in cluster.members if m in known and m not in claimed]
        if not members:
            continue
        claimed.update(members)
        node_id = unique_id(cluster.canonical_name, cluster.entity_type)
        canonical = cluster.canonical_name
        aliases = sorted({m for m in members if m != canonical})
        entities.append(
            ResolvedEntity(
                canonical_id=node_id,
                canonical_name=canonical,
                entity_type=cluster.entity_type,
                aliases=aliases,
                decision="merged" if len(members) > 1 else "single",
                rationale=cluster.rationale,
                confidence=cluster.confidence,
                provenance=spans_for(members),
            )
        )
        for member in members:
            surface_map.setdefault(normalize_surface(member), node_id)

    ambiguous_kept = []
    for group in result.ambiguous:
        valid = [m for m in group.surface_forms if m in known and m not in claimed]
        if valid:
            ambiguous_kept.append(
                group.model_copy(update={"surface_forms": valid})
            )

    # Every surface form not claimed by a cluster stays its own entity —
    # including the members of ambiguous groups. Nothing is silently dropped.
    for surface in index.surface_forms():
        if surface in claimed:
            continue
        for etype in sorted(index.types_of(surface)):
            node_id = unique_id(surface, etype)
            in_ambiguous = any(
                surface in g.surface_forms for g in ambiguous_kept
            )
            entities.append(
                ResolvedEntity(
                    canonical_id=node_id,
                    canonical_name=surface,
                    entity_type=etype,  # type: ignore[arg-type]
                    decision="ambiguous" if in_ambiguous else "single",
                    rationale=(
                        "left unmerged: flagged ambiguous by resolution"
                        if in_ambiguous
                        else None
                    ),
                    provenance=spans_for([surface]),
                )
            )
            surface_map.setdefault(normalize_surface(surface), node_id)
            claimed.add(surface)
            break  # one node per surface form; first type wins deterministically

    cleaned = ResolutionResult(
        clusters=result.clusters, ambiguous=ambiguous_kept, notes=result.notes
    )
    return entities, surface_map, cleaned, warnings
