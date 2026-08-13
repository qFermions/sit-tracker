"""End-to-end pipeline runner: documents → persistent knowledge graph."""

from __future__ import annotations

from pathlib import Path

from kgkit.assembly import assemble
from kgkit.client import Engine
from kgkit.config import KitConfig
from kgkit.extraction import extract_all, load_documents
from kgkit.graph_store import GraphStore
from kgkit.models import SourceDocument
from kgkit.resolution import resolve


def run_pipeline(
    engine: Engine,
    config: KitConfig,
    docs: list[SourceDocument],
) -> tuple[GraphStore, list[str]]:
    """documents → extraction → resolution → assembly. Returns (store, warnings)."""
    extractions, warnings = extract_all(engine, config, docs)
    entities, surface_map, resolution_raw, res_warnings = resolve(
        engine, config, extractions
    )
    warnings.extend(res_warnings)
    store, asm_warnings = assemble(
        extractions,
        entities,
        surface_map,
        docs,
        ambiguous=resolution_raw.ambiguous,
    )
    warnings.extend(asm_warnings)
    return store, warnings


def run_pipeline_dir(
    engine: Engine,
    config: KitConfig,
    docs_dir: str | Path,
    out_path: str | Path | None = None,
) -> tuple[GraphStore, list[str]]:
    docs = load_documents(docs_dir)
    store, warnings = run_pipeline(engine, config, docs)
    if out_path is not None:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        store.save(out_path)
    return store, warnings
