"""Export buyer-readable JSON Schemas from the Pydantic models.

Run from the kit root:  python tools/export_schemas.py
The schemas/ directory is generated output; models.py is the source of truth.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kgkit.models import (  # noqa: E402
    Answer,
    AnalystReport,
    EvalRunRecord,
    ExtractionResult,
    KnowledgeGraph,
    QueryPlan,
    ResolutionResult,
    SynthesisReport,
)

EXPORTS = {
    "extraction.schema.json": ExtractionResult,
    "resolution.schema.json": ResolutionResult,
    "graph.schema.json": KnowledgeGraph,
    "query.schema.json": QueryPlan,
    "answer.schema.json": Answer,
    "analyst_report.schema.json": AnalystReport,
    "synthesis.schema.json": SynthesisReport,
    "evaluation.schema.json": EvalRunRecord,
}


def expected_schemas() -> dict[str, dict]:
    return {
        filename: model.model_json_schema() for filename, model in EXPORTS.items()
    }


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "schemas"
    out_dir.mkdir(exist_ok=True)
    for filename, schema in expected_schemas().items():
        (out_dir / filename).write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote schemas/{filename}")


if __name__ == "__main__":
    main()
