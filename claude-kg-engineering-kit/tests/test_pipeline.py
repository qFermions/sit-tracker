import json

from kgkit.graph_store import GraphStore
from kgkit.pipeline import run_pipeline


def test_pipeline_end_to_end_offline(built, docs_by_id):
    store, warnings = built
    assert store.stats()["nodes"] == 10
    assert store.stats()["edges"] == 19
    errors = [
        i for i in store.validate(docs=docs_by_id) if i.startswith("ERROR:")
    ]
    assert errors == []


def test_graph_persists_and_reloads_identically(built, tmp_path):
    store, _ = built
    path = tmp_path / "graph.json"
    store.save(path)
    # The persisted artifact is plain, readable JSON.
    data = json.loads(path.read_text())
    assert data["schema_version"] == "1.0"
    assert {n["node_id"] for n in data["nodes"]} == {
        n.node_id for n in store.graph.nodes
    }
    reloaded = GraphStore.load(path)
    assert reloaded.graph.nodes == store.graph.nodes
    assert reloaded.graph.edges == store.graph.edges


def test_pipeline_is_deterministic_given_same_stage_outputs(engine, config, docs):
    a, _ = run_pipeline(engine, config, docs)
    b, _ = run_pipeline(engine, config, docs)
    assert a.graph.nodes == b.graph.nodes
    assert a.graph.edges == b.graph.edges
