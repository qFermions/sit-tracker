"""The engine boundary: how semantic stages talk to Claude.

Three engines implement the same tiny interface:

- :class:`AnthropicEngine` — live calls through the official SDK using
  structured outputs (``client.messages.parse`` with a Pydantic model).
- :class:`FixtureEngine` — replays recorded responses from JSON files, so the
  demo and the test suite run with no API key and no network. Fixture output
  is clearly labeled as canned; it is never presented as a live response.
- :class:`MockEngine` — in-memory programmable responses for tests.

Every downstream module depends only on :class:`Engine`, which is what makes
the whole pipeline testable offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from kgkit.config import KitConfig
from kgkit.models import slugify

M = TypeVar("M", bound=BaseModel)


class EngineError(RuntimeError):
    pass


class Engine:
    """Interface: run one semantic stage and get a validated model back."""

    name: str = "base"

    def complete(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_input: str,
        response_model: Type[M],
        key: Optional[str] = None,
    ) -> M:
        """``key`` is a stable identifier for this call (doc id, question id);
        the live engine ignores it, the fixture engine uses it for lookup."""
        raise NotImplementedError


class AnthropicEngine(Engine):
    name = "live"

    def __init__(self, config: Optional[KitConfig] = None):
        self.config = config or KitConfig()
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - import guard
            raise EngineError("pip install anthropic to use the live engine") from exc
        # Zero-arg client: resolves ANTHROPIC_API_KEY / auth profile itself.
        self._client = anthropic.Anthropic()

    def complete(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_input: str,
        response_model: Type[M],
        key: Optional[str] = None,
    ) -> M:
        model = self.config.model_for_stage(stage)
        response = self._client.messages.parse(
            model=model,
            max_tokens=self.config.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}],
            output_format=response_model,
        )
        if getattr(response, "stop_reason", None) == "refusal":
            raise EngineError(
                f"stage {stage}: the model declined this request "
                f"(stop_reason=refusal). Check stop_details on the response."
            )
        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise EngineError(
                f"stage {stage}: no parsed output returned "
                f"(stop_reason={getattr(response, 'stop_reason', '?')})"
            )
        return parsed


class FixtureEngine(Engine):
    """Replays recorded stage outputs from ``<fixtures>/<stage>/<key>.json``.

    These files are authored/recorded ahead of time and validated against the
    same Pydantic schemas as live output. They stand in for model calls so a
    buyer can run the full pipeline offline — they are fixtures, not live
    Claude responses, and are labeled as such everywhere.
    """

    name = "fixture"

    def __init__(self, fixtures_dir: str | Path):
        self.fixtures_dir = Path(fixtures_dir)
        if not self.fixtures_dir.is_dir():
            raise EngineError(f"fixtures directory not found: {self.fixtures_dir}")
        self.calls: list[tuple[str, str]] = []

    def complete(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_input: str,
        response_model: Type[M],
        key: Optional[str] = None,
    ) -> M:
        if key is None:
            raise EngineError(f"stage {stage}: fixture engine requires a key")
        path = self.fixtures_dir / stage / f"{slugify(key)}.json"
        if not path.is_file():
            raise EngineError(
                f"no fixture for stage={stage} key={key}: expected {path}"
            )
        self.calls.append((stage, key))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise EngineError(f"fixture {path} is invalid: {exc}") from exc


class MockEngine(Engine):
    """Programmable engine for tests: responses keyed by (stage, key)."""

    name = "mock"

    def __init__(self):
        self.responses: dict[tuple[str, Optional[str]], object] = {}
        self.calls: list[tuple[str, Optional[str]]] = []

    def add(self, stage: str, key: Optional[str], response: object) -> None:
        self.responses[(stage, key)] = response

    def complete(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_input: str,
        response_model: Type[M],
        key: Optional[str] = None,
    ) -> M:
        self.calls.append((stage, key))
        try:
            raw = self.responses[(stage, key)]
        except KeyError as exc:
            raise EngineError(f"mock has no response for ({stage}, {key})") from exc
        if isinstance(raw, response_model):
            return raw
        return response_model.model_validate(raw)


def run_with_repair(
    engine: Engine,
    *,
    stage: str,
    system_prompt: str,
    user_input: str,
    response_model: Type[M],
    key: Optional[str],
    validator: Callable[[M], list[str]],
    max_attempts: int,
) -> tuple[M, list[str]]:
    """Bounded validate-and-retry loop around one stage call.

    Attempt → validate → if issues remain and attempts are left, re-ask with
    the issues appended as feedback. The loop is strictly bounded by
    ``max_attempts`` extra tries; the caller decides what to do with the
    issues that survive (usually salvage + record).
    """
    attempt_input = user_input
    result = engine.complete(
        stage=stage,
        system_prompt=system_prompt,
        user_input=attempt_input,
        response_model=response_model,
        key=key,
    )
    issues = validator(result)
    attempts_used = 0
    # Fixture replay is deterministic — re-asking would return the same bytes.
    can_retry = engine.name == "live"
    while issues and can_retry and attempts_used < max_attempts:
        attempts_used += 1
        feedback = (
            f"{user_input}\n\n<previous_attempt_problems>\n"
            + "\n".join(f"- {i}" for i in issues)
            + "\n</previous_attempt_problems>\n"
            "Correct these problems. Only report what the source supports."
        )
        result = engine.complete(
            stage=stage,
            system_prompt=system_prompt,
            user_input=feedback,
            response_model=response_model,
            key=key,
        )
        issues = validator(result)
    return result, issues
