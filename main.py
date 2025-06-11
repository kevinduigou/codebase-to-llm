from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from application.ports import ClipboardPort, DirectoryRepositoryPort
from application.rules_service import RulesService
from application.recent_repository_service import RecentRepositoryService
from application.ignore_service import IgnoreService
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from domain.directory_tree import default_ignore_tokens
from infrastructure.filesystem_rules_repository import FileSystemRulesRepository
from infrastructure.filesystem_recent_repository import FileSystemRecentRepository
from infrastructure.filesystem_ignore_repository import FileSystemIgnoreRepository
from infrastructure.qt_clipboard_service import QtClipboardService
from interface.gui import MainWindow


def main() -> None:  # noqa: D401 (simple verb)
    app = QApplication(sys.argv)

    root = Path.cwd()
    repo: DirectoryRepositoryPort = FileSystemDirectoryRepository(
        root,
        list(default_ignore_tokens()),
    )
    rules_repo = FileSystemRulesRepository()
    rules_service = RulesService(rules_repo)
    recent_repo = FileSystemRecentRepository()
    recent_service = RecentRepositoryService(recent_repo)
    ignore_repo = FileSystemIgnoreRepository()
    ignore_service = IgnoreService(ignore_repo)
    clipboard: ClipboardPort = QtClipboardService()

    window = MainWindow(
        repo,
        clipboard,
        root,
        rules_service,
        recent_service,
        ignore_service,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
