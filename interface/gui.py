from __future__ import annotations

import sys
from pathlib import Path
from typing import Final, List
import os

from PySide6.QtCore import Qt, QMimeData, QUrl, QDir
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QTreeView,
    QWidget,
    QVBoxLayout,
    QAbstractItemView,
)

from application.copy_context import CopyContextUseCase
from application.ports import ClipboardPort, DirectoryRepositoryPort
from domain.result import Err
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from domain.directory_tree import should_ignore, get_ignore_tokens


class _FileListWidget(QListWidget):
    """Right‑panel list accepting drops from the tree view."""

    __slots__ = ("_root_path",)

    def __init__(self, root_path: Path):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # type: ignore[attr-defined]
        self._root_path = root_path

    def set_root_path(self, root_path: Path):
        self._root_path = root_path

    def _add_files_from_directory(self, directory: Path):
        """Recursively add all non-ignored files from the directory."""
        ignore_tokens = get_ignore_tokens(directory)
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            # Filter out ignored directories in-place
            dirs[:] = [
                d for d in dirs if not should_ignore(root_path / d, ignore_tokens)
            ]
            for file in files:
                file_path = root_path / file
                if not should_ignore(file_path, ignore_tokens):
                    try:
                        rel_path = file_path.relative_to(self._root_path)
                    except ValueError:
                        rel_path = file_path
                    self.addItem(str(rel_path))

    # -------------------------------------------------------------- DnD
    def dragEnterEvent(self, event: QDragEnterEvent):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):  # noqa: N802
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                ignore_tokens = get_ignore_tokens(self._root_path)
                if not should_ignore(path, ignore_tokens):
                    try:
                        rel_path = path.relative_to(self._root_path)
                    except ValueError:
                        rel_path = path
                    self.addItem(str(rel_path))
            elif path.is_dir():
                self._add_files_from_directory(path)
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)


class MainWindow(QMainWindow):
    """Qt main window binding infrastructure to application layer."""

    __slots__ = (
        "_tree_view",
        "_file_list",
        "_model",
        "_repo",
        "_clipboard",
        "_copy_context_use_case",
    )

    def __init__(
        self,
        repo: DirectoryRepositoryPort,
        clipboard: ClipboardPort,
        initial_root: Path,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Desktop Context Copier")
        self.resize(960, 600)

        self._repo: Final = repo
        self._clipboard: Final = clipboard
        self._copy_context_use_case: Final = CopyContextUseCase(repo, clipboard)

        splitter = QSplitter(Qt.Horizontal, self)  # type: ignore[attr-defined]
        splitter.setChildrenCollapsible(False)

        # --------------------------- left — directory tree
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Dirs | QDir.Files | QDir.Hidden)  # type: ignore[attr-defined]
        self._model.setRootPath(str(initial_root))
        self._tree_view = QTreeView()
        self._tree_view.setModel(self._model)
        self._tree_view.setRootIndex(self._model.index(str(initial_root)))
        self._tree_view.setDragEnabled(True)
        splitter.addWidget(self._tree_view)

        # --------------------------- right — dropped files list
        self._file_list = _FileListWidget(initial_root)
        splitter.addWidget(self._file_list)

        # --------------------------- central widget
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(splitter)
        self.setCentralWidget(central)

        # --------------------------- toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Choose directory action
        choose_dir_action = QAction("Choose Directory", self)
        choose_dir_action.triggered.connect(self._choose_directory)  # type: ignore[arg-type]
        toolbar.addAction(choose_dir_action)

        # Copy context button
        copy_btn = QPushButton("Copy Context")
        copy_btn.clicked.connect(self._copy_context)  # type: ignore[arg-type]
        toolbar.addWidget(copy_btn)

        # Delete selected button
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected)  # type: ignore[arg-type]
        toolbar.addWidget(delete_btn)

    # ──────────────────────────────────────────────────────────────────
    def _choose_directory(self):  # noqa: D401 (simple verb)
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            path = Path(directory)
            self._model.setRootPath(str(path))
            self._tree_view.setRootIndex(self._model.index(str(path)))
            # Re‑initialise repository for new root
            self._repo = FileSystemDirectoryRepository(path)  # type: ignore[assignment]
            self._copy_context_use_case = CopyContextUseCase(self._repo, self._clipboard)  # type: ignore[assignment]
            self._file_list.clear()
            self._file_list.set_root_path(path)

    def _copy_context(self):  # noqa: D401 (simple verb)
        files: List[Path] = [
            Path(item.text())
            for item in self._file_list.findItems("*", Qt.MatchWildcard)
        ]
        result = self._copy_context_use_case.execute(files)
        if result.is_err():
            QMessageBox.critical(self, "Copy Context Error", result.err())

    def _delete_selected(self) -> None:
        for item in self._file_list.selectedItems():
            row = self._file_list.row(item)
            self._file_list.takeItem(row)
