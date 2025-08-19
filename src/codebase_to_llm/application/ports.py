from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol
from openai import Stream
from codebase_to_llm.domain.api_key import ApiKeys, ApiKey, ApiKeyId
from codebase_to_llm.domain.user import (
    EmailAddress,
    User,
    UserName,
    UserId,
    ValidationToken,
)
from codebase_to_llm.domain.context_buffer import (
    ContextBuffer,
    ExternalSource,
    File as BufferFile,
    Snippet,
)
from codebase_to_llm.domain.prompt import Prompt, PromptVariable

from codebase_to_llm.domain.result import Result
from codebase_to_llm.domain.rules import Rules
from codebase_to_llm.domain.favorite_prompts import FavoritePrompts
from codebase_to_llm.domain.model import Models, Model, ModelId
from codebase_to_llm.domain.stored_file import StoredFile, StoredFileId
from codebase_to_llm.domain.directory import Directory, DirectoryId


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
    """Pure port for persisting / loading the user's custom rules."""

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
    def get_latest_repo(self) -> Result[Path, str]: ...  # pragma: no cover


class ExternalSourceRepositoryPort(Protocol):
    """Pure port to fetch data from external URLs."""

    def fetch_web_page(self, url: str) -> Result[str, str]: ...  # pragma: no cover

    def fetch_youtube_transcript(
        self, url: str, include_timestamps: bool = False
    ) -> Result[str, str]: ...  # pragma: no cover


class ContextBufferPort(Protocol):
    """Pure port to manage the context buffer."""

    def add_external_source(
        self, external_source: ExternalSource
    ) -> Result[None, str]: ...  # pragma: no cover
    def remove_external_source(
        self, url: str
    ) -> Result[None, str]: ...  # pragma: no cover

    def add_file(self, file: BufferFile) -> Result[None, str]: ...  # pragma: no cover
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
    def get_files(self) -> list[BufferFile]: ...  # pragma: no cover
    def get_snippets(self) -> list[Snippet]: ...  # pragma: no cover
    def get_context_buffer(self) -> ContextBuffer: ...  # pragma: no cover

    def clear(self) -> Result[None, str]: ...  # pragma: no cover
    def is_empty(self) -> bool: ...  # pragma: no cover
    def count_items(self) -> int: ...  # pragma: no cover


class FavoritePromptsRepositoryPort(Protocol):
    """Pure port for persisting favorite prompts."""

    def load_prompts(self) -> Result[FavoritePrompts, str]: ...  # pragma: no cover
    def save_prompts(
        self, prompts: FavoritePrompts
    ) -> Result[None, str]: ...  # pragma: no cover


class PromptRepositoryPort(Protocol):
    """Pure port to persist and retrieve the user prompt."""

    def set_prompt(self, prompt: Prompt) -> Result[None, str]: ...  # pragma: no cover
    def get_prompt(self) -> Result[Prompt | None, str]: ...  # pragma: no cover
    def get_variables_in_prompt(
        self,
    ) -> Result[list[PromptVariable], str]: ...  # pragma: no cover

    def set_prompt_variable(
        self, variable_key: str, content: str
    ) -> Result[None, str]: ...  # pragma: no cover


class ModelRepositoryPort(Protocol):
    """Pure port for persisting and loading models."""

    def load_models(self) -> Result[Models, str]: ...  # pragma: no cover
    def save_models(self, models: Models) -> Result[None, str]: ...  # pragma: no cover
    def find_model_by_id(
        self, model_id: ModelId
    ) -> Result[Model, str]: ...  # pragma: no cover


class ApiKeyRepositoryPort(Protocol):
    """Pure port for persisting and loading API keys."""

    def load_api_keys(self) -> Result[ApiKeys, str]: ...  # pragma: no cover
    def save_api_keys(
        self, api_keys: ApiKeys
    ) -> Result[None, str]: ...  # pragma: no cover
    def find_api_key_by_id(
        self, api_key_id: ApiKeyId
    ) -> Result[ApiKey, str]: ...  # pragma: no cover


class UserRepositoryPort(Protocol):
    """Pure port for user persistence and retrieval."""

    def add_user(self, user: User) -> Result[None, str]: ...  # pragma: no cover

    def find_by_name(self, name: UserName) -> Result[User, str]: ...  # pragma: no cover

    def find_by_email(
        self, email: EmailAddress
    ) -> Result[User, str]: ...  # pragma: no cover

    def find_by_validation_token(
        self, token: ValidationToken
    ) -> Result[User, str]: ...  # pragma: no cover

    def validate_user(self, user: User) -> Result[None, str]: ...  # pragma: no cover


class EmailSenderPort(Protocol):
    """Port for sending validation emails."""

    def send_validation_email(
        self, email: EmailAddress, token: ValidationToken
    ) -> Result[None, str]: ...  # pragma: no cover


class LLMAdapterPort(Protocol):
    """Pure port for LLM adapters."""

    def generate_response(
        self,
        prompt: str,
        model: str,
        api_key: ApiKey,
        previous_response_id: str | None = None,
    ) -> Result[Stream[Any], str]: ...  # pragma: no cover


class FileStoragePort(Protocol):
    """Port for persisting file contents."""

    def save(
        self, file: StoredFile, content: bytes
    ) -> Result[None, str]: ...  # pragma: no cover

    def load(self, file: StoredFile) -> Result[bytes, str]: ...  # pragma: no cover

    def delete(self, file: StoredFile) -> Result[None, str]: ...  # pragma: no cover


class FileRepositoryPort(Protocol):
    """Port for CRUD operations on file metadata and access rights."""

    def add(self, file: StoredFile) -> Result[None, str]: ...  # pragma: no cover

    def get(
        self, file_id: StoredFileId
    ) -> Result[StoredFile, str]: ...  # pragma: no cover

    def update(self, file: StoredFile) -> Result[None, str]: ...  # pragma: no cover

    def remove(
        self, file_id: StoredFileId
    ) -> Result[None, str]: ...  # pragma: no cover

    def list_for_user(
        self, owner_id: UserId
    ) -> Result[list[StoredFile], str]: ...  # pragma: no cover


class DirectoryStructureRepositoryPort(Protocol):
    """Port for CRUD operations on user directories."""

    def add(self, directory: Directory) -> Result[None, str]: ...  # pragma: no cover

    def get(
        self, directory_id: DirectoryId
    ) -> Result[Directory, str]: ...  # pragma: no cover

    def update(self, directory: Directory) -> Result[None, str]: ...  # pragma: no cover

    def remove(
        self, directory_id: DirectoryId
    ) -> Result[None, str]: ...  # pragma: no cover

    def list_for_user(
        self, owner_id: UserId
    ) -> Result[list[Directory], str]: ...  # pragma: no cover


class MetricsPort(Protocol):
    """Port for recording observability metrics."""

    def record_tokens(
        self, user: UserName, tokens: int
    ) -> Result[None, str]: ...  # pragma: no cover


class DownloadTaskPort(Protocol):
    """Port for long-running download tasks."""

    def enqueue_youtube_download(
        self, url: str, start: str, end: str, name: str, owner_id: str
    ) -> Result[str, str]: ...  # pragma: no cover

    def get_task_status(
        self, task_id: str
    ) -> Result[tuple[str, str | None], str]: ...  # pragma: no cover
