from __future__ import annotations

from pathlib import Path
from typing import Protocol

from domain.result import Result


class ClipboardPort(Protocol):
    """Abstract clipboard that can receive plain text."""

    def set_text(self, text: str) -> None:  # noqa: D401 (simple verb)
        ...  # pragma: no cover


class DirectoryRepositoryPort(Protocol):
    """Read‑only access to a directory tree and its files (pure queries)."""

    def build_tree(self) -> Result[str, str]: ...  # pragma: no cover

    def read_file(
        self, relative_path: Path
    ) -> Result[str, str]: ...  # pragma: no cover

class RulesRepositoryPort(Protocol):
    """Pure port for persisting / loading the user’s custom rules."""

    def load_rules(self) -> Result[str, str]: ...      # pragma: no cover
    def save_rules(self, rules: str) -> Result[None, str]: ...  # pragma: no cover
