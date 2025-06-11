from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from application.ports import ClipboardPort, DirectoryRepositoryPort
from application.rules_service import RulesService
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from infrastructure.filesystem_rules_repository import FileSystemRulesRepository
from infrastructure.qt_clipboard_service import QtClipboardService
from interface.gui import MainWindow


def main() -> None:  # noqa: D401 (simple verb)
    app = QApplication(sys.argv)

    root = Path.cwd()
    repo: DirectoryRepositoryPort = FileSystemDirectoryRepository(root)
    rules_repo = FileSystemRulesRepository()
    rules_service = RulesService(rules_repo)
    clipboard: ClipboardPort = QtClipboardService()

    window = MainWindow(repo, clipboard, root,rules_service)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
