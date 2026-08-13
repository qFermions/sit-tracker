"""Packaging hygiene: no secrets, valid data files, coherent prompts, clean ZIP."""

import json
import re
import zipfile
from pathlib import Path

from kgkit.prompts import load_prompt

# Real Anthropic keys are long base62-ish strings; the {16,} floor means the
# documentation placeholder "sk-ant-..." is not a match, an actual key is.
SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*['\"]?sk-ant-[A-Za-z0-9_\-]{16,}"),
]

TEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".txt", ".example"}


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if any(part in {".git", ".pytest_cache", "__pycache__", ".venv", "dist"}
               for part in path.parts):
            continue
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            yield path


def test_no_secrets_anywhere(kit_root):
    for path in iter_text_files(kit_root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(text), f"possible secret in {path}"


def test_no_dotenv_file_committed(kit_root):
    assert not (kit_root / ".env").exists()


def test_all_fixture_and_gold_files_are_valid_json(kit_root):
    for path in kit_root.rglob("*.json"):
        if any(part in {".git", "node_modules", "dist"} for part in path.parts):
            continue
        json.loads(path.read_text(encoding="utf-8"))  # raises on invalid


def test_all_stage_prompts_exist_and_are_versioned(kit_root):
    for name in [
        "extraction", "resolution", "query_planner", "answer",
        "analyst", "synthesizer",
    ]:
        info = load_prompt(name, prompts_dir=kit_root / "prompts")
        assert info.version != "0", f"{name}.md is missing its version header"
        assert len(info.text) > 200, f"{name}.md looks empty"


def test_schemas_match_current_models(kit_root):
    """schemas/*.json are exports of the Pydantic models — they must not drift."""
    schemas_dir = kit_root / "schemas"
    if not schemas_dir.is_dir():
        return  # exported later in the build; the export tool asserts freshness
    from tools.export_schemas import expected_schemas  # type: ignore

    for filename, schema in expected_schemas().items():
        on_disk = json.loads((schemas_dir / filename).read_text(encoding="utf-8"))
        assert on_disk == schema, f"{filename} is stale; re-run tools/export_schemas.py"


def test_dist_zip_is_clean_if_built(kit_root):
    zips = list((kit_root / "dist").glob("*.zip")) if (kit_root / "dist").is_dir() else []
    if not zips:
        return  # packaging phase not run yet
    for zip_path in zips:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            for name in names:
                assert ".git/" not in name, f"{zip_path.name} leaks git internals"
                assert "__pycache__" not in name, f"{zip_path.name} contains caches"
                assert not name.endswith(".env"), f"{zip_path.name} contains .env"
                assert "evals/runs/" not in name or name.endswith("runs/"), (
                    f"{zip_path.name} ships internal eval run logs"
                )
            root_files = {n.split("/", 1)[1] for n in names if "/" in n}
            for required in [
                "README.md", "QUICKSTART.md", "LICENSE", "pyproject.toml",
                "SOURCES.md", "LIMITATIONS.md",
            ]:
                assert required in root_files, f"{zip_path.name} misses {required}"
            for internal in ["PROJECT_STATE.md", "SALES_COPY.md"]:
                assert internal not in root_files, (
                    f"{zip_path.name} ships internal file {internal}"
                )
