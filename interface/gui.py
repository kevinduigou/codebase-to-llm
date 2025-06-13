from __future__ import annotations

import sys
from pathlib import Path
from typing import Final, List, Callable
import os
import re

from PySide6.QtCore import Qt, QMimeData, QUrl, QDir, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QTreeView,
    QWidget,
    QVBoxLayout,
    QAbstractItemView,
    QSizePolicy,
    QMenu,
    QToolButton,
    QTextEdit,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QInputDialog,
)

from application.copy_context import CopyContextUseCase
from application.ports import (
    ClipboardPort,
    DirectoryRepositoryPort,
)
from application.rules_service import RulesService
from application.recent_repository_service import RecentRepositoryService
from infrastructure.filesystem_recent_repository import FileSystemRecentRepository
from domain.result import Err, Result
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from domain.directory_tree import should_ignore, get_ignore_tokens


class _FileListWidget(QListWidget):
    """Right‑panel list accepting drops from the tree view."""

    __slots__ = ("_root_path", "_copy_context")

    def __init__(self, root_path: Path, copy_context: Callable[[], None]):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # type: ignore[attr-defined]
        self._root_path = root_path
        self._copy_context = copy_context
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_root_path(self, root_path: Path):
        self._root_path = root_path

    # ----------------------------------------------------------- context menu
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
                    # Prevent duplicates
                    if not self.findItems(str(rel_path), Qt.MatchFlag.MatchExactly):
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
                    # Prevent duplicates
                    if not self.findItems(str(rel_path), Qt.MatchFlag.MatchExactly):
                        self.addItem(str(rel_path))
            elif path.is_dir():
                self._add_files_from_directory(path)
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)


class RulesDialog(QDialog):
    """Simple dialog to edit rules."""

    __slots__ = ("_edit",)

    def __init__(self, current_rules: str, rules_service: RulesService) -> None:
        super().__init__()
        self.setWindowTitle("Edit Rules")
        layout = QVBoxLayout(self)
        self._edit = QPlainTextEdit()
        self._edit.setPlainText(current_rules)
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)
        self._rules_service = rules_service

    def text(self) -> str:
        return self._edit.toPlainText()

    def accept(self) -> None:
        self._rules_service.save_rules(self._edit.toPlainText())
        return super().accept()


class MainWindow(QMainWindow):
    """Qt main window binding infrastructure to application layer."""

    __slots__ = (
        "_tree_view",
        "_file_list",
        "_model",
        "_repo",
        "_clipboard",
        "_copy_context_use_case",
        "_recent_service",
        "_recent_menu",
        "user_request_text_edit",
        "_rules",
        "_include_rules_checkbox",
        "_include_tree_checkbox",
        "_filter_model",
        "_name_filter_edit",
    )

    def __init__(
        self,
        repo: DirectoryRepositoryPort,
        clipboard: ClipboardPort,
        initial_root: Path,
        rules_service: RulesService,
        recent_service: RecentRepositoryService,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Desktop Context Copier")
        self.resize(960, 600)

        self._repo = repo
        self._clipboard: Final = clipboard
        self._copy_context_use_case = CopyContextUseCase(repo, clipboard)
        self._rules_service = rules_service
        self._recent_service = recent_service

        # Load persisted rules if available
        self._rules = ""
        rules_result = self._rules_service.load_rules()
        if rules_result.is_ok():
            self._rules = rules_result.ok() or ""

        splitter = QSplitter(Qt.Horizontal, self)  # type: ignore[attr-defined]
        splitter.setChildrenCollapsible(False)

        # --------------------------- left — directory tree
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Dirs | QDir.Files | QDir.Hidden)  # type: ignore[attr-defined]
        self._model.setRootPath(str(initial_root))

        self._filter_model = QSortFilterProxyModel()
        self._filter_model.setSourceModel(self._model)
        self._filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._filter_model.setRecursiveFilteringEnabled(True)
        self._filter_model.setFilterKeyColumn(0)

        self._tree_view = QTreeView()
        self._tree_view.setModel(self._filter_model)
        self._tree_view.setRootIndex(
            self._filter_model.mapFromSource(self._model.index(str(initial_root)))
        )
        self._tree_view.setDragEnabled(True)

        self._name_filter_edit = QLineEdit()
        self._name_filter_edit.setPlaceholderText("Filter files (regex)")
        self._name_filter_edit.textChanged.connect(self._filter_by_name)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._name_filter_edit)
        left_layout.addWidget(self._tree_view)

        splitter.addWidget(left_panel)

        # --------------------------- right — dropped files list
        self._file_list = _FileListWidget(initial_root, self._copy_context)
        splitter.addWidget(self._file_list)

        # --------------------------- central widget
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(splitter)
        self.user_request_text_edit = QPlainTextEdit()
        self.user_request_text_edit.setPlaceholderText(
            "Describe your need or the bug here..."
        )
        self.user_request_text_edit.setFixedHeight(100)
        layout.addWidget(self.user_request_text_edit)
        self.setCentralWidget(central)

        # --------------------------- toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Choose directory action
        choose_dir_action = QAction("Choose Directory", self)
        choose_dir_action.triggered.connect(self._choose_directory)  # type: ignore[arg-type]
        toolbar.addAction(choose_dir_action)


        # Recent repositories dropdown
        self._recent_menu = QMenu(self)
        recent_button = QToolButton(self)
        recent_button.setText("Open Recently")
        recent_button.setMenu(self._recent_menu)
        recent_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar.addWidget(recent_button)
        self._populate_recent_menu()

        # Add spacer to push settings cog to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Settings dropdown with cog icon
        settings_icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogDetailedView
        )
        settings_menu = QMenu(self)
        edit_rules_action = QAction("Edit Rules", self)
        edit_rules_action.triggered.connect(self._open_settings)  # type: ignore[arg-type]
        settings_menu.addAction(edit_rules_action)
        settings_button = QToolButton(self)
        settings_button.setIcon(settings_icon)
        settings_button.setMenu(settings_menu)
        settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        settings_button.setToolTip("Settings")
        toolbar.addWidget(settings_button)

        # --------------------------- bottom bar for copy context button
        bottom_bar_layout = QHBoxLayout()
        self._include_tree_checkbox = QCheckBox("Include Tree Context")
        self._include_tree_checkbox.setChecked(True)
        self._include_rules_checkbox = QCheckBox("Include Rules")
        self._include_rules_checkbox.setChecked(True)
        # Copy context button
        copy_btn = QPushButton("Copy Context")
        copy_btn.clicked.connect(self._copy_context)  # type: ignore[arg-type]
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected)  # type: ignore[arg-type]
        # Bottom bar layout for "Copy Context" button
        bottom_bar_layout.addWidget(self._include_tree_checkbox)
        bottom_bar_layout.addWidget(self._include_rules_checkbox)
        bottom_bar_layout.addStretch(1)  # Pushes everything else to the right
        bottom_bar_layout.addWidget(delete_btn)
        bottom_bar_layout.addWidget(copy_btn)  # Button sits flush right

        layout.addLayout(bottom_bar_layout)  # Attach to the main vertical layout

        # Set up context menu for user_request_text_edit
        self.user_request_text_edit.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.user_request_text_edit.customContextMenuRequested.connect(
            self._show_user_request_context_menu
        )

    # ──────────────────────────────────────────────────────────────────

    def _choose_directory(self):  # noqa: D401 (simple verb)
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            path = Path(directory)
            self._model.setRootPath(str(path))
            self._filter_model.invalidateFilter()
            self._tree_view.setRootIndex(
                self._filter_model.mapFromSource(self._model.index(str(path)))
            )
            # Re‑initialise repository for new root
            self._repo = FileSystemDirectoryRepository(path)  # type: ignore[assignment]
            self._copy_context_use_case = CopyContextUseCase(self._repo, self._clipboard)  # type: ignore[assignment]
            self._file_list.clear()
            self._file_list.set_root_path(path)
            self._recent_service.add_path(path)
            self._populate_recent_menu()

    def _open_recent(self, path: Path) -> None:
        self._model.setRootPath(str(path))
        self._filter_model.invalidateFilter()
        self._tree_view.setRootIndex(
            self._filter_model.mapFromSource(self._model.index(str(path)))
        )
        self._repo = FileSystemDirectoryRepository(path)  # type: ignore[assignment]
        self._copy_context_use_case = CopyContextUseCase(self._repo, self._clipboard)  # type: ignore[assignment]
        self._file_list.clear()
        self._file_list.set_root_path(path)
        self._recent_service.add_path(path)
        self._populate_recent_menu()

    def _populate_recent_menu(self) -> None:
        self._recent_menu.clear()
        result = self._recent_service.load_recent()
        if result.is_err():
            return
        paths = result.ok() or []
        for path in paths:
            action = QAction(str(path), self)
            action.triggered.connect(
                lambda checked=False, p=path: self._open_recent(p)
            )  # type: ignore[arg-type]
            self._recent_menu.addAction(action)

    def _copy_context(self):  # noqa: D401 (simple verb)
        files: List[Path] = [
            Path(item.text())
            for item in self._file_list.findItems("*", Qt.MatchFlag.MatchWildcard)
        ]
        user_text = self.user_request_text_edit.toPlainText().strip()
        rules_text = self._rules if self._include_rules_checkbox.isChecked() else None
        include_tree = self._include_tree_checkbox.isChecked()
        result = self._copy_context_use_case.execute(
            files, rules_text, user_text, include_tree
        )

        if result.is_err():
            QMessageBox.critical(self, "Copy\u00a0Context\u00a0Error", result.err())

    def _delete_selected(self) -> None:
        self._file_list.delete_selected()

    def _open_settings(self) -> None:
        result_load_rules: Result[str, str] = self._rules_service.load_rules()
        if result_load_rules.is_ok():
            dialog = RulesDialog(result_load_rules.ok() or "", self._rules_service)
        else:
            dialog = RulesDialog("", self._rules_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._rules = dialog.text()

    def _show_user_request_context_menu(self, pos) -> None:
        menu = QMenu(self)
        copy_context_action = QAction("Copy Context", self)
        copy_context_action.triggered.connect(self._copy_context)  # type: ignore[arg-type]
        menu.addAction(copy_context_action)
        menu.exec_(self.user_request_text_edit.mapToGlobal(pos))

    def _filter_by_name(self, text: str) -> None:
        if text:
            regex = QRegularExpression(text)
            self._filter_model.setFilterRegularExpression(regex)
        else:
            self._filter_model.setFilterRegularExpression(QRegularExpression())
