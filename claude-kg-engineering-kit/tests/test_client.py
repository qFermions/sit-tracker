import pytest
from pydantic import BaseModel

from kgkit.client import Engine, EngineError, FixtureEngine, MockEngine, run_with_repair


class Reply(BaseModel):
    text: str


class CountingLiveEngine(Engine):
    """Pretends to be a live engine so the repair loop will re-ask it."""

    name = "live"

    def __init__(self, reply: Reply):
        self.calls = 0
        self.reply = reply

    def complete(self, *, stage, system_prompt, user_input, response_model, key=None):
        self.calls += 1
        return self.reply


def test_fixture_engine_reports_missing_fixture(tmp_path):
    (tmp_path / "somestage").mkdir()
    engine = FixtureEngine(tmp_path)
    with pytest.raises(EngineError, match="no fixture"):
        engine.complete(
            stage="somestage",
            system_prompt="",
            user_input="",
            response_model=Reply,
            key="nope",
        )


def test_fixture_engine_validates_against_schema(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "k.json").write_text('{"wrong_field": 1}')
    engine = FixtureEngine(tmp_path)
    with pytest.raises(EngineError, match="invalid"):
        engine.complete(
            stage="s", system_prompt="", user_input="", response_model=Reply, key="k"
        )


def test_repair_loop_is_bounded_for_live_engines():
    engine = CountingLiveEngine(Reply(text="always wrong"))
    result, issues = run_with_repair(
        engine,
        stage="s",
        system_prompt="",
        user_input="input",
        response_model=Reply,
        key=None,
        validator=lambda r: ["still wrong"],
        max_attempts=2,
    )
    assert engine.calls == 3  # 1 initial + exactly max_attempts repairs, never more
    assert issues == ["still wrong"]


def test_repair_loop_stops_when_valid():
    engine = CountingLiveEngine(Reply(text="fine"))
    result, issues = run_with_repair(
        engine,
        stage="s",
        system_prompt="",
        user_input="input",
        response_model=Reply,
        key=None,
        validator=lambda r: [],
        max_attempts=2,
    )
    assert engine.calls == 1
    assert issues == []


def test_repair_loop_never_retries_deterministic_fixtures(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "k.json").write_text('{"text": "wrong"}')
    engine = FixtureEngine(tmp_path)
    result, issues = run_with_repair(
        engine,
        stage="s",
        system_prompt="",
        user_input="",
        response_model=Reply,
        key="k",
        validator=lambda r: ["bad"],
        max_attempts=5,
    )
    assert engine.calls == [("s", "k")]  # exactly one call — retrying is pointless
    assert issues == ["bad"]


def test_mock_engine_validates_dict_payloads():
    engine = MockEngine()
    engine.add("s", "k", {"text": "hello"})
    out = engine.complete(
        stage="s", system_prompt="", user_input="", response_model=Reply, key="k"
    )
    assert out.text == "hello"
