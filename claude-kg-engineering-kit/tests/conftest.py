import pytest
from pathlib import Path

from kgkit.client import FixtureEngine
from kgkit.config import KitConfig
from kgkit.extraction import load_documents
from kgkit.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "competitive_intelligence"


@pytest.fixture(scope="session")
def kit_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def demo_dir() -> Path:
    return DEMO


@pytest.fixture(scope="session")
def docs():
    return load_documents(DEMO / "documents")


@pytest.fixture(scope="session")
def docs_by_id(docs):
    return {d.doc_id: d for d in docs}


@pytest.fixture(scope="session")
def config():
    return KitConfig()


@pytest.fixture(scope="session")
def engine():
    return FixtureEngine(DEMO / "fixtures")


@pytest.fixture(scope="session")
def built(engine, config, docs):
    """The demo pipeline run once for the whole test session (offline)."""
    return run_pipeline(engine, config, docs)


@pytest.fixture(scope="session")
def store(built):
    return built[0]
