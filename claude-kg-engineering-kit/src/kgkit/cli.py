"""kgkit command line.

Every command works offline with --engine fixture (the default for the demo
and evals). --engine live requires ANTHROPIC_API_KEY and spends real tokens.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from kgkit.agents.orchestrator import run_competitive_analysis
from kgkit.client import AnthropicEngine, Engine, EngineError, FixtureEngine  # noqa: F401
from kgkit.config import KitConfig, api_key_present
from kgkit.evaluation import (
    compare_runs,
    eval_extraction,
    eval_qa,
    eval_resolution,
    extraction_mismatch_details,
    record_run,
)
from kgkit.extraction import extract_all, load_documents
from kgkit.graph_store import GraphStore
from kgkit.pipeline import run_pipeline, run_pipeline_dir
from kgkit.prompts import load_prompt
from kgkit.provenance import citation_report
from kgkit.query import answer_question
from kgkit.resolution import resolve


def kit_root() -> Path:
    """The kit checkout root (where examples/ and prompts/ live)."""
    for candidate in (Path.cwd(), Path(__file__).resolve().parents[2]):
        if (candidate / "examples").is_dir() and (candidate / "prompts").is_dir():
            return candidate
    raise SystemExit(
        "Run kgkit from the kit's root directory (the one containing "
        "examples/ and prompts/)."
    )


DEMO_DIR = "examples/competitive_intelligence"


def build_engine(args) -> Engine:
    if args.engine == "live":
        if not api_key_present():
            raise SystemExit(
                "--engine live needs ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN "
                "(see .env.example). Use --engine fixture to run offline."
            )
        return AnthropicEngine(KitConfig())
    fixtures = Path(args.fixtures) if args.fixtures else kit_root() / DEMO_DIR / "fixtures"
    return FixtureEngine(fixtures)


def _print_warnings(warnings: list[str]) -> None:
    for w in warnings:
        print(f"  ! {w}")


def cmd_run(args) -> int:
    engine = build_engine(args)
    store, warnings = run_pipeline_dir(
        engine, KitConfig(), args.docs, out_path=args.out
    )
    print(f"Graph written to {args.out}")
    print(f"  {store.stats()}")
    _print_warnings(warnings)
    return 0


def cmd_validate(args) -> int:
    store = GraphStore.load(args.graph)
    docs = None
    if args.docs:
        docs = {d.doc_id: d for d in load_documents(args.docs)}
    issues = store.validate(docs=docs)
    errors = [i for i in issues if i.startswith("ERROR:")]
    for issue in issues:
        print(issue)
    print(f"{store.stats()} -> {len(errors)} error(s)")
    return 1 if errors else 0


def cmd_query(args) -> int:
    engine = build_engine(args)
    store = GraphStore.load(args.graph)
    key = args.key or "adhoc"
    answer, pack, warnings = answer_question(
        engine, KitConfig(), store, args.question, key=key
    )
    print(f"Q: {args.question}\n")
    print(f"A: {answer.answer}\n")
    if answer.insufficient_evidence:
        print("(insufficient evidence in the graph)")
    elif answer.cited_edge_ids:
        print("Evidence trail:")
        print(citation_report(store, answer.cited_edge_ids))
    _print_warnings(warnings)
    return 0


def cmd_demo(args) -> int:
    root = kit_root()
    demo = root / DEMO_DIR
    engine = build_engine(args)
    config = KitConfig()

    print(f"[1/4] Building the graph from {demo / 'documents'} "
          f"(engine: {engine.name})")
    docs = load_documents(demo / "documents")
    store, warnings = run_pipeline(engine, config, docs)
    out_dir = Path(args.out) if args.out else demo / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = out_dir / "graph.json"
    store.save(graph_path)
    print(f"      graph: {store.stats()} -> {graph_path}")
    _print_warnings(warnings)

    print("\n[2/4] Answering questions with graph evidence")
    questions = json.loads((demo / "questions.json").read_text(encoding="utf-8"))
    strategic = None
    for q in questions:
        if q.get("strategic"):
            strategic = q
            continue
        answer, pack, q_warnings = answer_question(
            engine, config, store, q["question"], key=q["question_id"]
        )
        print(f"\n  Q ({q['question_id']}): {q['question']}")
        print(f"  A: {answer.answer}")
        if answer.cited_edge_ids and not answer.insufficient_evidence:
            print(f"  cites: {', '.join(answer.cited_edge_ids)}")
        _print_warnings(q_warnings)

    print("\n[3/4] Specialist analysts + synthesizer (shared graph)")
    if strategic is None:
        raise SystemExit("questions.json has no strategic question")
    analysis = run_competitive_analysis(
        engine, config, store, strategic["question"]
    )
    for role, report in sorted(analysis.reports.items()):
        print(f"\n  [{role} analyst]")
        for finding in report.findings:
            print(f"   - {finding.claim}  [{', '.join(finding.edge_ids)}]")

    print(f"\n[4/4] Strategic synthesis")
    print(f"\n  Q: {strategic['question']}")
    synth = analysis.synthesis
    print(f"\n  {synth.assessment}\n")
    print(f"  confidence: {synth.confidence}")
    if synth.caveats:
        print(f"  caveats: {synth.caveats}")
    print("\n  Full evidence trail (claims -> edges -> document quotes):")
    cited = sorted({eid for f in synth.key_findings for eid in f.edge_ids})
    print("  " + citation_report(store, cited).replace("\n", "\n  "))
    _print_warnings(analysis.warnings)

    if engine.name == "fixture":
        print(
            "\nNote: this run used recorded fixture outputs for the Claude "
            "stages (no API key, no network). Re-run with --engine live to "
            "produce everything with real model calls."
        )
    return 0


def _eval_prompt_versions(names: list[str]) -> dict[str, str]:
    versions = {}
    for name in names:
        info = load_prompt(name)
        versions[name] = info.version_label
    return versions


def cmd_eval_run(args) -> int:
    root = kit_root()
    demo = root / DEMO_DIR
    evals_dir = root / "evals"
    runs_dir = evals_dir / "runs"
    engine = build_engine(args)
    config = KitConfig()
    suites = (
        ["extraction", "resolution", "qa"] if args.suite == "all" else [args.suite]
    )

    docs = load_documents(demo / "documents")
    extractions, warnings = extract_all(engine, config, docs)
    outputs = []

    if "extraction" in suites:
        gold_entities = json.loads(
            (evals_dir / "gold_extraction.json").read_text(encoding="utf-8")
        )
        gold_relations = json.loads(
            (evals_dir / "gold_relations.json").read_text(encoding="utf-8")
        )
        metrics = eval_extraction(extractions, gold_entities, gold_relations)
        path = record_run(
            runs_dir,
            "extraction",
            engine.name,
            _eval_prompt_versions(["extraction"]),
            metrics=metrics,
            details=warnings
            + extraction_mismatch_details(extractions, gold_entities, gold_relations),
        )
        outputs.append(("extraction", metrics, {}, path))

    if "resolution" in suites:
        entities, _, _, res_warnings = resolve(engine, config, extractions)
        gold = json.loads(
            (evals_dir / "gold_resolution.json").read_text(encoding="utf-8")
        )
        metrics, details = eval_resolution(entities, gold)
        path = record_run(
            runs_dir,
            "resolution",
            engine.name,
            _eval_prompt_versions(["extraction", "resolution"]),
            metrics=metrics,
            details=details + res_warnings,
        )
        outputs.append(("resolution", metrics, {}, path))

    if "qa" in suites:
        store, _ = run_pipeline(engine, config, docs)
        gold = json.loads(
            (evals_dir / "gold_queries.json").read_text(encoding="utf-8")
        )
        results = []
        answer_warnings: list[str] = []
        for g in gold:
            answer, pack, q_warnings = answer_question(
                engine, config, store, g["question"], key=g["question_id"]
            )
            answer_warnings.extend(f"{g['question_id']}: {w}" for w in q_warnings)
            results.append(
                {"question_id": g["question_id"], "answer": answer, "evidence": pack}
            )
        scalars, details = eval_qa(store, results, gold)
        details = answer_warnings + details
        path = record_run(
            runs_dir,
            "qa",
            engine.name,
            _eval_prompt_versions(
                ["extraction", "resolution", "query_planner", "answer"]
            ),
            scalar_metrics=scalars,
            details=details,
        )
        outputs.append(("qa", {}, scalars, path))

    for suite, metrics, scalars, path in outputs:
        print(f"\n[{suite}] -> {path}")
        for name, m in metrics.items():
            print(f"  {name}: P={m.precision:.3f} R={m.recall:.3f} F1={m.f1:.3f}")
        for name, v in scalars.items():
            print(f"  {name}: {v:.3f}")
    return 0


def cmd_eval_compare(args) -> int:
    print(compare_runs(args.run_a, args.run_b))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kgkit",
        description="Claude Knowledge Graph Engineering Kit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_engine_args(p):
        p.add_argument("--engine", choices=["fixture", "live"], default="fixture")
        p.add_argument("--fixtures", help="fixtures dir (default: demo fixtures)")

    p = sub.add_parser("run", help="documents dir -> graph.json")
    p.add_argument("--docs", required=True)
    p.add_argument("--out", required=True)
    add_engine_args(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("validate", help="check graph integrity")
    p.add_argument("graph")
    p.add_argument("--docs", help="documents dir to verify citation quotes against")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("query", help="ask a question against a graph")
    p.add_argument("graph")
    p.add_argument("question")
    p.add_argument("--key", help="stable question id (required for fixtures)")
    add_engine_args(p)
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("demo", help="run the competitive-intelligence demo")
    p.add_argument("--out", help="output dir (default: examples/.../output)")
    add_engine_args(p)
    p.set_defaults(func=cmd_demo)

    p_eval = sub.add_parser("eval", help="evaluation harness")
    eval_sub = p_eval.add_subparsers(dest="eval_command", required=True)
    p = eval_sub.add_parser("run", help="run an eval suite and record it")
    p.add_argument(
        "--suite",
        choices=["extraction", "resolution", "qa", "all"],
        default="all",
    )
    add_engine_args(p)
    p.set_defaults(func=cmd_eval_run)
    p = eval_sub.add_parser("compare", help="diff two recorded runs")
    p.add_argument("run_a")
    p.add_argument("run_b")
    p.set_defaults(func=cmd_eval_compare)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except EngineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
