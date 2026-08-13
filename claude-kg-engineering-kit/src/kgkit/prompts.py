"""Prompt loading with explicit versioning.

Prompts are Markdown files in prompts/ so buyers can read and edit them.
Each file may start with a header line ``<!-- version: N -->``. Evaluation
runs record both the declared version and the content hash, so two eval runs
can always be compared prompt-for-prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from kgkit.config import find_prompts_dir
from kgkit.models import sha256_text

_VERSION_RE = re.compile(r"<!--\s*version:\s*([^\s]+)\s*-->")


@dataclass(frozen=True)
class PromptInfo:
    name: str
    version: str
    sha256: str
    text: str

    @property
    def version_label(self) -> str:
        return f"{self.name}@v{self.version}+{self.sha256[:8]}"


def load_prompt(name: str, prompts_dir: Path | None = None) -> PromptInfo:
    directory = prompts_dir or find_prompts_dir()
    path = directory / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"prompt file not found: {path}")
    text = path.read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    version = match.group(1) if match else "0"
    return PromptInfo(name=name, version=version, sha256=sha256_text(text), text=text)
