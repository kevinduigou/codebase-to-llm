# Widgets for the GUI components

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QPainter,
    QFontMetrics,
)
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QMenu,
    QTextEdit,
    QAbstractItemView,
)

from codebase_to_llm.domain.directory_tree import should_ignore, get_ignore_tokens




class ContextBufferWidget(QListWidget):
    """Right panel list accepting drops from the tree view."""

    __slots__ = ("_root_path", "_copy_context")

    def __init__(self, root_path: Path, copy_context: Callable[[], None]):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # type: ignore[attr-defined]
        self._root_path = root_path
        self._copy_context = copy_context
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_root_path(self, root_path: Path) -> None:
        self._root_path = root_path

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        delete_action = QAction("Delete Selected", self)
        delete_action.triggered.connect(self.delete_selected)  # type: ignore[arg-type]
        menu.addAction(delete_action)
        copy_context_action = QAction("Copy Context", self)
        copy_context_action.triggered.connect(self._copy_context)  # type: ignore[arg-type]
        menu.addAction(copy_context_action)
        menu.exec_(self.mapToGlobal(pos))

    def delete_selected(self) -> None:
        for item in self.selectedItems():
            row = self.row(item)
            self.takeItem(row)

    def add_snippet(self, path: Path, start: int, end: int, text: str) -> None:
        try:
            rel_path = path.relative_to(self._root_path)
        except ValueError:
            rel_path = path
        label = f"{rel_path}:{start}:{end}"
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, text)
        self.addItem(item)

    def add_file(self, path: Path) -> None:
        try:
            rel_path = path.relative_to(self._root_path)
        except ValueError:
            rel_path = path
        if not self.findItems(str(rel_path), Qt.MatchFlag.MatchExactly):
            self.addItem(str(rel_path))

    def _add_files_from_directory(self, directory: Path) -> None:
        ignore_tokens = get_ignore_tokens(directory)
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
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
                    if not self.findItems(str(rel_path), Qt.MatchFlag.MatchExactly):
                        self.addItem(str(rel_path))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                ignore_tokens = get_ignore_tokens(self._root_path)
                if not should_ignore(path, ignore_tokens):
                    try:
                        rel_path = path.relative_to(self._root_path)
                    except ValueError:
                        rel_path = path
                    if not self.findItems(str(rel_path), Qt.MatchFlag.MatchExactly):
                        self.addItem(str(rel_path))
            elif path.is_dir():
                self._add_files_from_directory(path)
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)



