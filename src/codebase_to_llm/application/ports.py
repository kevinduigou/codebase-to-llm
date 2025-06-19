from __future__ import annotations

from pathlib import Path
from typing import Protocol

from codebase_to_llm.domain.context_buffer import (
    ContextBuffer,
    ExternalSource,
    File,
    Snippet,
)
from codebase_to_llm.domain.prompt import Prompt

from codebase_to_llm.domain.result import Result
from codebase_to_llm.domain.rules import Rules


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

    def load_rules(self) -> Result[Rules, str]: ...  # pragma: no cover
    def save_rules(self, rules: Rules) -> Result[None, str]: ...  # pragma: no cover

    def update_rule_enabled(
        self, name: str, enabled: bool
    ) -> Result[None, str]: ...  # pragma: no cover


class RecentRepositoryPort(Protocol):
    """Pure port for persisting recently opened repository paths."""

    def load_paths(self) -> Result[list[Path], str]: ...  # pragma: no cover
    def save_paths(
        self, paths: list[Path]
    ) -> Result[None, str]: ...  # pragma: no cover


class ExternalSourceRepositoryPort(Protocol):
    """Pure port to fetch data from external URLs."""

    def fetch_web_page(self, url: str) -> Result[str, str]: ...  # pragma: no cover

    def fetch_youtube_transcript(
        self, url: str
    ) -> Result[str, str]: ...  # pragma: no cover


class ContextBufferPort(Protocol):
    """Pure port to manage the context buffer."""

    def add_external_source(
        self, url: str, text: str
    ) -> Result[None, str]: ...  # pragma: no cover
    def remove_external_source(
        self, url: str
    ) -> Result[None, str]: ...  # pragma: no cover

    def add_file(self, file: File) -> Result[None, str]: ...  # pragma: no cover
    def remove_file(self, path: Path) -> Result[None, str]: ...  # pragma: no cover

    def add_snippet(
        self, snippet: Snippet
    ) -> Result[None, str]: ...  # pragma: no cover
    def remove_snippet(
        self, path: Path, start: int, end: int
    ) -> Result[None, str]: ...  # pragma: no cover

    def get_external_sources(
        self,
    ) -> list[ExternalSource]: ...  # pragma: no cover
    def get_files(self) -> list[File]: ...  # pragma: no cover
    def get_snippets(self) -> list[Snippet]: ...  # pragma: no cover
    def get_context_buffer(self) -> ContextBuffer: ...  # pragma: no cover

    def clear(self) -> Result[None, str]: ...  # pragma: no cover
    def is_empty(self) -> bool: ...  # pragma: no cover
    def count_items(self) -> int: ...  # pragma: no cover


class PromptRepositoryPort(Protocol):
    """Pure port to persist and retrieve the user prompt."""

    def set_prompt(self, prompt: Prompt) -> Result[None, str]: ...  # pragma: no cover
    def get_prompt(self) -> Result[Prompt | None, str]: ...  # pragma: no cover
