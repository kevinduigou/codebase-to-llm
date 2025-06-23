from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from codebase_to_llm.application.ports import (
    ClipboardPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    ExternalSourceRepositoryPort,
)

from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)

from codebase_to_llm.infrastructure.filesystem_recent_repository import (
    FileSystemRecentRepository,
)
from codebase_to_llm.infrastructure.filesystem_rules_repository import RulesRepository
from codebase_to_llm.infrastructure.filesystem_favorite_prompts_repository import (
    FavoritePromptsRepository,
)
from codebase_to_llm.infrastructure.in_memory_context_buffer_repository import (
    InMemoryContextBufferRepository,
)
from codebase_to_llm.infrastructure.in_memory_prompt_repository import (
    InMemoryPromptRepository,
)
from codebase_to_llm.infrastructure.qt_clipboard_service import QtClipboardService
from codebase_to_llm.infrastructure.url_external_source_repository import (
    UrlExternalSourceRepository,
)
from codebase_to_llm.interface.main_window import MainWindow


def main() -> None:  # noqa: D401 (simple verb)
    app = QApplication(sys.argv)

    rules_repo = RulesRepository()
    prompts_repo = FavoritePromptsRepository()
    recent_repo = FileSystemRecentRepository()

    root: Path | None = None
    latest_repo_result = recent_repo.get_latest_repo()
    if latest_repo_result.is_ok():
        root = latest_repo_result.ok()

    if root is None or not root.exists():
        # Default to current working directory
        root = Path.cwd()

    repo: DirectoryRepositoryPort = FileSystemDirectoryRepository(root)
    clipboard: ClipboardPort = QtClipboardService()
    context_buffer: ContextBufferPort = InMemoryContextBufferRepository()
    prompt_repo = InMemoryPromptRepository()
    external_repo: ExternalSourceRepositoryPort = UrlExternalSourceRepository()
    window = MainWindow(
        repo,
        clipboard,
        root,
        rules_repo,
        prompts_repo,
        recent_repo,
        external_repo,
        context_buffer,
        prompt_repo,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
