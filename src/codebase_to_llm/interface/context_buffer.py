# Widgets for the GUI components

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
)
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QMenu,
    QAbstractItemView,
)

from codebase_to_llm.application.uc_add_code_snippet_to_context_buffer import (
    AddCodeSnippetToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_external_source import (
    AddExternalSourceToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_file_to_context_buffer import (
    AddFileToContextBufferUseCase,
)
from codebase_to_llm.application.uc_remove_elmts_from_context_buffer import (
    RemoveElementsFromContextBufferUseCase,
)
from codebase_to_llm.domain.directory_tree import should_ignore, get_ignore_tokens
from codebase_to_llm.domain.result import Result


class ContextBufferWidget(QListWidget):
    """Right panel list accepting drops from the tree view."""

    __slots__ = (
        "_root_path",
        "_copy_context",
        "_context_buffer",
        "_selected_elmts",
        "_add_code_snippet_to_context_buffer",
    )

    def __init__(
        self,
        root_path: Path,
        copy_context: Callable[[], None],
        add_file_to_context_buffer: AddFileToContextBufferUseCase,
        remove_elmts_from_context_buffer: RemoveElementsFromContextBufferUseCase,
        add_external_source_to_context_buffer: AddExternalSourceToContextBufferUseCase,
        add_code_snippet_to_context_buffer: AddCodeSnippetToContextBufferUseCase,
    ):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # type: ignore[attr-defined]
        self._root_path = root_path
        self._copy_context = copy_context
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._add_file_to_context_buffer = add_file_to_context_buffer
        self._remove_elmts_from_context_buffer = remove_elmts_from_context_buffer
        self._add_external_source_to_context_buffer = (
            add_external_source_to_context_buffer
        )
        self._selected_elmts: list = []
        self._add_code_snippet_to_context_buffer = add_code_snippet_to_context_buffer

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
            item_id = item.data(Qt.ItemDataRole.UserRole)  # Can be a file path or a url
            self._remove_elmts_from_context_buffer.execute([item_id])
            self.takeItem(row)

    def add_snippet(self, path: Path, start: int, end: int, text: str) -> None:
        try:
            rel_path = path.relative_to(self._root_path)
        except ValueError:
            rel_path = path

        result = self._add_code_snippet_to_context_buffer.execute(
            path, start, end, text
        )
        if result.is_err():
            return

        label = f"{rel_path}:{start}:{end}"
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, f"snippet:{label}")

        self.addItem(item)

    def add_file(self, path: Path) -> None:
        try:
            rel_path = path.relative_to(self._root_path)
        except ValueError:
            rel_path = path
        result = self._add_file_to_context_buffer.execute(path)
        if result.is_err():
            return
        if not self.findItems(str(rel_path), Qt.MatchFlag.MatchExactly):
            result = self._add_file_to_context_buffer.execute(path)
            if result.is_err():
                return
            item = QListWidgetItem(str(rel_path))
            item.setData(
                Qt.ItemDataRole.UserRole, f"file:{str(path)}"
            )  # or just path if you want
            self.addItem(item)

    def add_external_source(self, url: str) -> Result[str, str]:
        result = self._add_external_source_to_context_buffer.execute(url.strip())
        if result.is_ok():
            item = QListWidgetItem(url)
            item.setData(Qt.ItemDataRole.UserRole, f"external_source:{url}")
            self.addItem(item)
        return result

    def _add_files_from_directory(self, directory: Path) -> str | None:
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
                        result = self._add_file_to_context_buffer.execute(file_path)
                        if result.is_err():
                            return result.err()
                        item = QListWidgetItem(str(rel_path))
                        item.setData(Qt.ItemDataRole.UserRole, f"file:{str(file_path)}")
                        self.addItem(item)
        return None

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
                        result = self._add_file_to_context_buffer.execute(path)
                        if result.is_err():
                            continue
                        item = QListWidgetItem(str(rel_path))
                        item.setData(Qt.ItemDataRole.UserRole, f"file:{str(path)}")
                        self.addItem(item)
            elif path.is_dir():
                self._add_files_from_directory(path)
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
