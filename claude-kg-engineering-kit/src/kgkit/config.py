"""Runtime configuration.

Model choices are environment-configurable so the kit never hard-codes a
single model. Defaults were verified against Anthropic's model catalog on
2026-08-13 (see SOURCES.md #4): a fast/cheap model for high-volume
extraction, a stronger model for judgment-heavy stages.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_FAST_MODEL = "claude-haiku-4-5"
DEFAULT_QUALITY_MODEL = "claude-opus-5"

# Which model tier each semantic stage uses by default.
STAGE_TIER = {
    "extraction": "fast",
    "resolution": "quality",
    "query_planner": "quality",
    "answer": "quality",
    "analyst": "quality",
    "synthesizer": "quality",
}


@dataclass
class KitConfig:
    fast_model: str = field(
        default_factory=lambda: os.environ.get("KGKIT_FAST_MODEL", DEFAULT_FAST_MODEL)
    )
    quality_model: str = field(
        default_factory=lambda: os.environ.get(
            "KGKIT_QUALITY_MODEL", DEFAULT_QUALITY_MODEL
        )
    )
    # Cap for thinking + output combined on models with default-on thinking
    # (e.g. claude-opus-5); 16000 keeps non-streaming requests inside SDK
    # timeouts while leaving judgment stages room to think.
    max_tokens: int = 16000
    # Bounded repair: how many corrective re-asks a stage gets before the
    # pipeline salvages what verified and records the drops. Never infinite.
    max_repair_attempts: int = 2

    def model_for_stage(self, stage: str) -> str:
        tier = STAGE_TIER.get(stage, "quality")
        return self.fast_model if tier == "fast" else self.quality_model


def api_key_present() -> bool:
    """True when a credential the SDK can use is visibly configured.

    The zero-arg Anthropic() client also resolves stored auth profiles; this
    check only gates the CLI's error message, it is not the auth mechanism.
    """
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def find_prompts_dir() -> Path:
    """Locate the prompts/ directory (env override, cwd, then repo layout)."""
    env = os.environ.get("KGKIT_PROMPTS_DIR")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(Path.cwd() / "prompts")
    candidates.append(Path(__file__).resolve().parents[2] / "prompts")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find the prompts/ directory. Run from the kit root or set "
        "KGKIT_PROMPTS_DIR."
    )
