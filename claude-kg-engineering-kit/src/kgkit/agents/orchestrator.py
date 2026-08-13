"""Orchestrator-workers over a shared graph (see SOURCES.md #2).

The persistent knowledge graph is the shared world model. Each analyst is a
worker with one bounded question; each queries the same graph (semantic
planning + deterministic retrieval) and reports findings that must cite edge
ids from its own retrieved evidence. The synthesizer may use only what the
analysts and the graph produced — its citations are verified against the
union of retrieved evidence, so the final strategic read is always traceable
back to source documents.

Design note: the three analysts are one implementation with different bounded
questions, not three copies of the same file. Their prompts and validation
are identical; only the question differs — so a config dict is the honest
representation. (This simplifies the suggested pricing.py/product.py/
financial.py layout; nothing else changed.)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kgkit.client import Engine, run_with_repair
from kgkit.config import KitConfig
from kgkit.graph_store import GraphStore
from kgkit.models import AnalystReport, EvidencePack, SynthesisReport
from kgkit.prompts import load_prompt
from kgkit.provenance import verify_citations
from kgkit.query import plan_query, retrieve

ANALYST_ROLES: dict[str, str] = {
    "pricing": (
        "What pricing facts are recorded in the graph: current prices, price "
        "changes (with before/after values and timing), and which company and "
        "product each applies to?"
    ),
    "product": (
        "What product capability facts are recorded in the graph: capabilities "
        "added, removed, or retained, which products compete, and any evidence "
        "about how customers value those capabilities?"
    ),
    "financial": (
        "What financial facts are recorded in the graph: margins, cost "
        "pressures, and any stated links between costs and pricing decisions?"
    ),
}


@dataclass
class CompetitiveAnalysis:
    question: str
    reports: dict[str, AnalystReport] = field(default_factory=dict)
    evidence: dict[str, EvidencePack] = field(default_factory=dict)
    synthesis: SynthesisReport | None = None
    warnings: list[str] = field(default_factory=list)


def _strip_uncited(report: AnalystReport, allowed: set[str]) -> AnalystReport:
    findings = []
    for finding in report.findings:
        valid = [eid for eid in finding.edge_ids if eid in allowed]
        if valid:
            findings.append(finding.model_copy(update={"edge_ids": valid}))
    return report.model_copy(update={"findings": findings})


def run_analyst(
    engine: Engine,
    config: KitConfig,
    store: GraphStore,
    role: str,
) -> tuple[AnalystReport, EvidencePack, list[str]]:
    if role not in ANALYST_ROLES:
        raise ValueError(f"unknown analyst role: {role}")
    question = ANALYST_ROLES[role]
    plan, plan_issues = plan_query(
        engine, config, store, question, key=f"analyst-{role}"
    )
    pack = retrieve(store, question, plan)
    warnings = [f"{role} planner: {i}" for i in plan_issues]

    if not pack.edges:
        return (
            AnalystReport(role=role, question=question, insufficient_evidence=True),
            pack,
            warnings,
        )

    prompt = load_prompt("analyst")
    allowed = {e.edge_id for e in pack.edges}
    user_input = (
        f"<role>{role} analyst</role>\n"
        f"<question>{question}</question>\n\n"
        f"<evidence>\n{pack.rendered}\n</evidence>"
    )

    def validator(r: AnalystReport) -> list[str]:
        issues = []
        for i, finding in enumerate(r.findings):
            if not finding.edge_ids:
                issues.append(f"finding[{i}] has no citations")
            issues.extend(verify_citations(store, finding.edge_ids, allowed))
        return issues

    report, issues = run_with_repair(
        engine,
        stage="analyst",
        system_prompt=prompt.text,
        user_input=user_input,
        response_model=AnalystReport,
        key=role,
        validator=validator,
        max_attempts=config.max_repair_attempts,
    )
    if issues:
        warnings.extend(f"{role} analyst: {i}" for i in issues)
        report = _strip_uncited(report, allowed)
    if report.role != role:
        report = report.model_copy(update={"role": role})
    return report, pack, warnings


def synthesize(
    engine: Engine,
    config: KitConfig,
    store: GraphStore,
    question: str,
    reports: dict[str, AnalystReport],
    packs: dict[str, EvidencePack],
) -> tuple[SynthesisReport, list[str]]:
    allowed: set[str] = set()
    edge_index = {}
    for pack in packs.values():
        for edge in pack.edges:
            allowed.add(edge.edge_id)
            edge_index[edge.edge_id] = edge
    rendered_union = store.render_edges(
        sorted(edge_index.values(), key=lambda e: e.edge_id)
    )

    report_blocks = []
    for role in sorted(reports):
        r = reports[role]
        lines = [f'<analyst role="{role}">']
        if r.insufficient_evidence:
            lines.append("(reported insufficient evidence)")
        for finding in r.findings:
            lines.append(f"- {finding.claim}  [cites: {', '.join(finding.edge_ids)}]")
        lines.append("</analyst>")
        report_blocks.append("\n".join(lines))

    user_input = (
        f"<question>{question}</question>\n\n"
        + "\n\n".join(report_blocks)
        + f"\n\n<evidence>\n{rendered_union}\n</evidence>"
    )

    prompt = load_prompt("synthesizer")

    def validator(s: SynthesisReport) -> list[str]:
        issues = []
        if not s.key_findings:
            issues.append("synthesis has no cited key findings")
        for i, finding in enumerate(s.key_findings):
            if not finding.edge_ids:
                issues.append(f"key_finding[{i}] has no citations")
            issues.extend(verify_citations(store, finding.edge_ids, allowed))
        return issues

    synthesis, issues = run_with_repair(
        engine,
        stage="synthesizer",
        system_prompt=prompt.text,
        user_input=user_input,
        response_model=SynthesisReport,
        key="synthesis",
        validator=validator,
        max_attempts=config.max_repair_attempts,
    )
    warnings = []
    if issues:
        warnings.extend(f"synthesizer: {i}" for i in issues)
        findings = []
        for finding in synthesis.key_findings:
            valid = [eid for eid in finding.edge_ids if eid in allowed]
            if valid:
                findings.append(finding.model_copy(update={"edge_ids": valid}))
        synthesis = synthesis.model_copy(update={"key_findings": findings})
    if not synthesis.key_findings:
        # No claim survived citation checking — the prose must not survive
        # either. Same rule as the answer path: unsupported means unsupported.
        warnings.append(
            "synthesizer: no cited finding survived verification; assessment replaced"
        )
        synthesis = SynthesisReport(
            assessment=(
                "Insufficient evidence: no synthesis claim could be grounded in "
                "the retrieved graph evidence."
            ),
            key_findings=[],
            confidence="low",
            caveats="The synthesizer produced no machine-verifiable citations.",
        )
    return synthesis, warnings


def run_competitive_analysis(
    engine: Engine,
    config: KitConfig,
    store: GraphStore,
    question: str,
    roles: list[str] | None = None,
) -> CompetitiveAnalysis:
    """Orchestrate: bounded analysts in sequence, then verified synthesis."""
    result = CompetitiveAnalysis(question=question)
    for role in roles or list(ANALYST_ROLES):
        report, pack, warnings = run_analyst(engine, config, store, role)
        result.reports[role] = report
        result.evidence[role] = pack
        result.warnings.extend(warnings)
    synthesis, warnings = synthesize(
        engine, config, store, question, result.reports, result.evidence
    )
    result.synthesis = synthesis
    result.warnings.extend(warnings)
    return result
