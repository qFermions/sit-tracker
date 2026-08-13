"""Stage 1 — Extraction: source passages → verified candidate facts.

Claude does the semantic reading; everything checkable is checked in code:
every mention and fact must carry a verbatim quote that actually appears in
the source document, and unverifiable items are dropped (and reported) after
a bounded repair loop.
"""

from __future__ import annotations

from pathlib import Path

from kgkit.client import Engine, run_with_repair
from kgkit.config import KitConfig
from kgkit.models import ExtractionResult, SourceDocument
from kgkit.prompts import PromptInfo, load_prompt
from kgkit.provenance import salvage_extraction, verify_extraction

STAGE = "extraction"


def load_documents(docs_dir: str | Path) -> list[SourceDocument]:
    """Read every .md/.txt file in a directory as one source document."""
    docs = []
    for path in sorted(Path(docs_dir).glob("*")):
        if path.suffix.lower() not in (".md", ".txt"):
            continue
        text = path.read_text(encoding="utf-8")
        title = path.stem
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        docs.append(SourceDocument(doc_id=path.stem, title=title, text=text))
    if not docs:
        raise FileNotFoundError(f"no .md/.txt documents found in {docs_dir}")
    return docs


def build_extraction_input(doc: SourceDocument) -> str:
    return (
        f'<document id="{doc.doc_id}" title="{doc.title}">\n'
        f"{doc.text}\n"
        f"</document>"
    )


def extract_document(
    engine: Engine,
    config: KitConfig,
    doc: SourceDocument,
    prompt: PromptInfo | None = None,
) -> tuple[ExtractionResult, list[str]]:
    """Extract one document. Returns the verified result plus warnings about
    anything that had to be dropped or repaired."""
    prompt = prompt or load_prompt("extraction")
    result, issues = run_with_repair(
        engine,
        stage=STAGE,
        system_prompt=prompt.text,
        user_input=build_extraction_input(doc),
        response_model=ExtractionResult,
        key=doc.doc_id,
        validator=lambda r: verify_extraction(r, doc),
        max_attempts=config.max_repair_attempts,
    )
    warnings: list[str] = []
    if issues:
        result, dropped = salvage_extraction(result, doc)
        warnings.extend(f"{doc.doc_id}: {d}" for d in dropped)
    # The pipeline, not the model, owns the doc_id.
    if result.doc_id != doc.doc_id:
        result = result.model_copy(update={"doc_id": doc.doc_id})
    return result, warnings


def extract_all(
    engine: Engine,
    config: KitConfig,
    docs: list[SourceDocument],
) -> tuple[dict[str, ExtractionResult], list[str]]:
    prompt = load_prompt("extraction")
    results: dict[str, ExtractionResult] = {}
    warnings: list[str] = []
    for doc in docs:
        result, doc_warnings = extract_document(engine, config, doc, prompt)
        results[doc.doc_id] = result
        warnings.extend(doc_warnings)
    return results, warnings
