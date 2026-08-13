"""Stage 4 — Query: multi-hop questions with evidence for every claim.

Three separated steps, exactly as the architecture demands:

1. **Planning** (semantic): Claude decides which entities/relations matter.
2. **Retrieval** (deterministic): plain BFS traversal collects the evidence.
3. **Synthesis** (semantic, verified): Claude answers using only the
   retrieved evidence and must cite edge ids; citations are checked in code,
   invalid ones are stripped, and an unsupported answer is downgraded to
   "insufficient evidence" rather than passed along.

If the graph has no evidence, the model is never called — the kit answers
"insufficient evidence" deterministically instead of letting model memory
fill the gap.
"""

from __future__ import annotations

from kgkit.client import Engine, run_with_repair
from kgkit.config import KitConfig
from kgkit.graph_store import GraphStore
from kgkit.models import Answer, EvidencePack, QueryPlan
from kgkit.prompts import load_prompt
from kgkit.provenance import verify_citations

INSUFFICIENT = (
    "Insufficient evidence: the knowledge graph does not contain the facts "
    "needed to answer this question."
)


def plan_query(
    engine: Engine,
    config: KitConfig,
    store: GraphStore,
    question: str,
    key: str,
) -> tuple[QueryPlan, list[str]]:
    prompt = load_prompt("query_planner")
    known_entities = "\n".join(
        f"- {n.name} ({n.entity_type})"
        + (f" aka {', '.join(n.aliases)}" if n.aliases else "")
        for n in sorted(store.graph.nodes, key=lambda n: n.node_id)
    )
    known_predicates = ", ".join(
        sorted({e.predicate for e in store.graph.edges})
    )
    user_input = (
        f"<question>{question}</question>\n\n"
        f"<graph_entities>\n{known_entities}\n</graph_entities>\n\n"
        f"<graph_relations>{known_predicates}</graph_relations>"
    )

    def validator(plan: QueryPlan) -> list[str]:
        issues = []
        if not plan.entities:
            issues.append("plan lists no entities to start from")
        unknown = [e for e in plan.entities if not store.find_nodes(e)]
        if unknown and len(unknown) == len(plan.entities):
            issues.append(
                f"none of the planned entities exist in the graph: {unknown}"
            )
        return issues

    plan, issues = run_with_repair(
        engine,
        stage="query_planner",
        system_prompt=prompt.text,
        user_input=user_input,
        response_model=QueryPlan,
        key=key,
        validator=validator,
        max_attempts=config.max_repair_attempts,
    )
    if plan.max_hops < 1:
        plan = plan.model_copy(update={"max_hops": 1})
    if plan.max_hops > 4:  # bounded traversal, always
        plan = plan.model_copy(update={"max_hops": 4})
    return plan, issues


def retrieve(store: GraphStore, question: str, plan: QueryPlan) -> EvidencePack:
    """Deterministic evidence collection from a plan."""
    seeds: set[str] = set()
    for name in plan.entities:
        for node in store.find_nodes(name):
            seeds.add(node.node_id)
    edges = store.traverse(
        sorted(seeds), max_hops=plan.max_hops, predicates=plan.predicates or None
    )
    return EvidencePack(
        question=question,
        seed_node_ids=sorted(seeds),
        edges=edges,
        rendered=store.render_edges(edges),
    )


def answer_question(
    engine: Engine,
    config: KitConfig,
    store: GraphStore,
    question: str,
    key: str,
) -> tuple[Answer, EvidencePack, list[str]]:
    """Plan → retrieve → answer, with citation verification."""
    plan, plan_issues = plan_query(engine, config, store, question, key)
    pack = retrieve(store, question, plan)
    warnings = [f"planner: {i}" for i in plan_issues]

    if not pack.edges:
        return (
            Answer(answer=INSUFFICIENT, insufficient_evidence=True),
            pack,
            warnings,
        )

    prompt = load_prompt("answer")
    allowed = {e.edge_id for e in pack.edges}
    user_input = (
        f"<question>{question}</question>\n\n"
        f"<evidence>\n{pack.rendered}\n</evidence>"
    )

    answer, issues = run_with_repair(
        engine,
        stage="answer",
        system_prompt=prompt.text,
        user_input=user_input,
        response_model=Answer,
        key=key,
        validator=lambda a: (
            []
            if a.insufficient_evidence
            else (
                ["answer cites no edges — every material claim needs a citation"]
                if not a.cited_edge_ids
                else verify_citations(store, a.cited_edge_ids, allowed)
            )
        ),
        max_attempts=config.max_repair_attempts,
    )

    if issues and not answer.insufficient_evidence:
        # Strip citations that failed verification rather than trusting them.
        valid = [
            eid
            for eid in answer.cited_edge_ids
            if eid in allowed and store.get_edge(eid) is not None
        ]
        warnings.extend(f"answer: {i}" for i in issues)
        if valid:
            answer = answer.model_copy(update={"cited_edge_ids": valid})
        else:
            answer = Answer(answer=INSUFFICIENT, insufficient_evidence=True)
    if answer.insufficient_evidence and answer.cited_edge_ids:
        # An insufficient-evidence answer carries no verified claims, so it
        # gets no citations either — nothing unchecked may look cited.
        warnings.append(
            "answer: dropped citations attached to an insufficient-evidence answer"
        )
        answer = answer.model_copy(update={"cited_edge_ids": []})
    return answer, pack, warnings
