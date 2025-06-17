from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from codebase_to_llm.application.ports import ClipboardPort, DirectoryRepositoryPort
from codebase_to_llm.application.recent_repository_service import (
    RecentRepositoryService,
)
from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)
from codebase_to_llm.infrastructure.filesystem_rules_repository import (
    FileSystemRulesRepository,
)
from codebase_to_llm.infrastructure.filesystem_recent_repository import (
    FileSystemRecentRepository,
)
from codebase_to_llm.infrastructure.qt_clipboard_service import QtClipboardService
from codebase_to_llm.infrastructure.url_external_source_repository import (
    UrlExternalSourceRepository,
)
from codebase_to_llm.interface.main_window import MainWindow


def main() -> None:  # noqa: D401 (simple verb)
    app = QApplication(sys.argv)

    root = Path.cwd()
    repo: DirectoryRepositoryPort = FileSystemDirectoryRepository(root)
    rules_repo = FileSystemRulesRepository()
    recent_repo = FileSystemRecentRepository()
    recent_service = RecentRepositoryService(recent_repo)
    clipboard: ClipboardPort = QtClipboardService()

    window = MainWindow(
        repo,
        clipboard,
        root,
        rules_repo,
        recent_service,
        UrlExternalSourceRepository(),
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
