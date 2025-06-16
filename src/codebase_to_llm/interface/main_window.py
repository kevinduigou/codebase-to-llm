"""Main application window for the desktop tool."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Final, List, Callable, cast

from PySide6.QtCore import (
    Qt,
    QDir,
    QSortFilterProxyModel,
    QRegularExpression,
    QRect,
    QSize,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
    QDialog,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QTreeView,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QMenu,
    QToolButton,
    QPlainTextEdit,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QLabel,
)

from codebase_to_llm.application.copy_context import CopyContextUseCase
from codebase_to_llm.application.ports import ClipboardPort, DirectoryRepositoryPort
from codebase_to_llm.application.recent_repository_service import RecentRepositoryService
from codebase_to_llm.infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from codebase_to_llm.infrastructure.filesystem_recent_repository import FileSystemRecentRepository
from codebase_to_llm.infrastructure.filesystem_rules_repository import FileSystemRulesRepository
from codebase_to_llm.domain.result import Result
from codebase_to_llm.domain.selected_text import SelectedText

from .widgets import _FileListWidget, _FilePreviewWidget
from .rules_dialogs import RulesManagerDialog


class MainWindow(QMainWindow):
    """Qt main window binding infrastructure to application layer."""

    __slots__ = (
        "_tree_view",
        "_file_preview",
        "_file_list",
        "_model",
        "_repo",
        "_clipboard",
        "_copy_context_use_case",
        "_recent_service",
        "_rules_repo",
        "_recent_menu",
        "user_request_text_edit",
        "_rules",
        "_include_rules_checkboxes",
        "_include_tree_checkbox",
        "_filter_model",
        "_name_filter_edit",
        "_toggle_preview_btn",
        "_preview_panel",
        "_rules_checkbox_container",
        "_rules_checkbox_layout",
    )

    def __init__(
        self,
        repo: DirectoryRepositoryPort,
        clipboard: ClipboardPort,
        initial_root: Path,
        rules_repo: FileSystemRulesRepository,
        recent_service: RecentRepositoryService,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Desktop Context Copier")
        self.resize(1200, 700)

        self._repo = repo
        self._clipboard: Final = clipboard
        self._copy_context_use_case = CopyContextUseCase(repo, clipboard)
        self._rules_repo = rules_repo
        self._recent_service = recent_service

        self._rules: str = ""
        rules_result = self._rules_repo.load_rules()
        if rules_result.is_ok():
            rules_val = rules_result.ok()
            assert rules_val is not None
            self._rules = rules_val.to_text()

        splitter = QSplitter(Qt.Horizontal, self)  # type: ignore[attr-defined]
        splitter.setChildrenCollapsible(False)

        # --------------------------- left — directory tree
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Dirs | QDir.Files | QDir.Hidden)  # type: ignore[attr-defined]
        self._model.setRootPath(str(initial_root))

        self._filter_model = QSortFilterProxyModel()
        self._filter_model.setSourceModel(self._model)
        self._filter_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._filter_model.setRecursiveFilteringEnabled(True)
        self._filter_model.setFilterKeyColumn(0)

        self._tree_view = QTreeView()
        self._tree_view.setModel(self._filter_model)
        self._tree_view.setRootIndex(
            self._filter_model.mapFromSource(self._model.index(str(initial_root)))
        )
        self._tree_view.setDragEnabled(True)
        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)

        self._name_filter_edit = QLineEdit()
        self._name_filter_edit.setPlaceholderText("Filter files (regex)")
        self._name_filter_edit.textChanged.connect(self._filter_by_name)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        tree_title = QLabel("Directory Tree")
        tree_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        tree_title.setToolTip(
            "Browse and navigate through your project's directory structure. Drag files to the right panel to include them in the context."
        )
        self._toggle_preview_btn = QToolButton(self)
        self._toggle_preview_btn.setText("Show File Preview")
        self._toggle_preview_btn.setCheckable(True)
        self._toggle_preview_btn.setChecked(False)
        self._toggle_preview_btn.toggled.connect(self._toggle_preview)

        title_layout = QHBoxLayout()
        title_layout.addWidget(tree_title)
        title_layout.addWidget(self._toggle_preview_btn)
        title_layout.addStretch()

        left_layout.addLayout(title_layout)
        left_layout.addWidget(self._name_filter_edit)
        left_layout.addWidget(self._tree_view)

        splitter.addWidget(left_panel)

        # --------------------------- right — dropped files list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        buffer_title = QLabel("Context Buffer")
        buffer_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        buffer_title.setToolTip(
            "Files and text snippets that will be included in the context. Drag files from the directory tree to add them here."
        )
        right_layout.addWidget(buffer_title)

        self._file_list = _FileListWidget(initial_root, self._copy_context)
        right_layout.addWidget(self._file_list)

        splitter.addWidget(right_panel)

        # --------------------------- middle — file preview
        self._file_preview = _FilePreviewWidget(self._file_list.add_snippet)
        self._preview_panel = QWidget()
        preview_layout = QVBoxLayout(self._preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_title = QLabel("File Preview")
        preview_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        preview_title.setToolTip(
            "View and select text from files. Double-click files in the directory tree to preview them here. Selected text can be added to the context buffer."
        )
        preview_layout.addWidget(preview_title)

        preview_layout.addWidget(self._file_preview)
        splitter.insertWidget(1, self._preview_panel)
        self._preview_panel.setVisible(False)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 2)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(splitter)
        self.user_request_text_edit = QPlainTextEdit()
        self.user_request_text_edit.setPlaceholderText("Describe your need or the bug here...")
        self.user_request_text_edit.setFixedHeight(100)
        layout.addWidget(self.user_request_text_edit)
        self.setCentralWidget(central)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        choose_dir_action = QAction("Choose Directory", self)
        choose_dir_action.triggered.connect(self._choose_directory)  # type: ignore[arg-type]
        toolbar.addAction(choose_dir_action)

        self._recent_menu = QMenu(self)
        recent_button = QToolButton(self)
        recent_button.setText("Open Recently")
        recent_button.setMenu(self._recent_menu)
        recent_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar.addWidget(recent_button)
        self._populate_recent_menu()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        settings_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
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

        bottom_bar_layout = QHBoxLayout()
        self._include_tree_checkbox = QCheckBox("Include Tree Context")
        self._include_tree_checkbox.setChecked(True)
        self._include_rules_checkboxes: dict[str, QCheckBox] = {}
        self._rules_checkbox_container = QWidget()
        self._rules_checkbox_layout = QHBoxLayout(self._rules_checkbox_container)
        self._rules_checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self._rules_checkbox_layout.setSpacing(4)
        self._refresh_rules_checkboxes()
        copy_btn = QPushButton("Copy Context in clipboard")
        copy_btn.clicked.connect(self._copy_context)  # type: ignore[arg-type]
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected)  # type: ignore[arg-type]
        bottom_bar_layout.addWidget(self._include_tree_checkbox)
        bottom_bar_layout.addWidget(self._rules_checkbox_container)
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(delete_btn)
        bottom_bar_layout.addWidget(copy_btn)

        layout.addLayout(bottom_bar_layout)

        self.user_request_text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.user_request_text_edit.customContextMenuRequested.connect(
            self._show_user_request_context_menu
        )

        self._tree_view.doubleClicked.connect(self._handle_tree_double_click)  # type: ignore[arg-type]

    # ---------------------------------------------------------------------
    # Preview logic
    def _handle_tree_double_click(self, proxy_index) -> None:
        source_index = self._filter_model.mapToSource(proxy_index)
        file_path = Path(self._model.filePath(source_index))
        if file_path.is_file():
            self._file_preview.load_file(file_path)
            self._preview_panel.setVisible(True)
            if hasattr(self, "_toggle_preview_btn"):
                self._toggle_preview_btn.setChecked(True)
        else:
            self._file_preview.clear()

    def _show_tree_context_menu(self, pos) -> None:
        index = self._tree_view.indexAt(pos)
        if not index.isValid():
            return
        source_index = self._filter_model.mapToSource(index)
        file_path = Path(self._model.filePath(source_index))
        if not file_path.is_file():
            return
        menu = QMenu(self)
        preview_action = QAction("Open Preview", self)
        preview_action.triggered.connect(lambda checked=False, p=file_path: self._file_preview.load_file(p))
        menu.addAction(preview_action)
        add_action = QAction("Add to Context Buffer", self)
        add_action.triggered.connect(lambda checked=False, p=file_path: self._file_list.add_file(p))
        menu.addAction(add_action)
        menu.exec_(self._tree_view.viewport().mapToGlobal(pos))

    def _choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            path = Path(directory)
            self._model.setRootPath(str(path))
            self._filter_model.invalidateFilter()
            self._tree_view.setRootIndex(
                self._filter_model.mapFromSource(self._model.index(str(path)))
            )
            self._repo = FileSystemDirectoryRepository(path)  # type: ignore[assignment]
            self._copy_context_use_case = CopyContextUseCase(self._repo, self._clipboard)  # type: ignore[assignment]
            self._file_list.clear()
            self._file_list.set_root_path(path)
            self._file_preview.clear()
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
        self._file_preview.clear()
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
            action.triggered.connect(lambda checked=False, p=path: self._open_recent(p))  # type: ignore[arg-type]
            self._recent_menu.addAction(action)

    def _copy_context(self) -> None:  # noqa: D401
        files: List[Path] = []
        snippets: List[SelectedText] = []
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                text_data = str(data)
                label = item.text()
                try:
                    path_str, start_str, end_str = label.rsplit(":", 2)
                    snippet_result = SelectedText.try_create(Path(path_str), int(start_str), int(end_str), text_data)
                    if snippet_result.is_ok():
                        snippet = snippet_result.ok()
                        assert snippet is not None
                        snippets.append(snippet)
                except Exception:
                    continue
            else:
                files.append(Path(item.text()))
        user_text = self.user_request_text_edit.toPlainText().strip()
        from codebase_to_llm.domain.rules import Rules

        checked_rule_names = [name for name, cb in self._include_rules_checkboxes.items() if cb.isChecked()]
        rules_obj = None
        if self._rules:
            rules_result = self._rules_repo.load_rules()
            if rules_result.is_ok():
                all_rules_obj = rules_result.ok()
                assert all_rules_obj is not None
                filtered_rules = tuple(
                    rule for rule in all_rules_obj.rules() if rule.name() in checked_rule_names
                )
                if filtered_rules:
                    rules_obj = Rules(filtered_rules)
        include_tree = self._include_tree_checkbox.isChecked()
        result = self._copy_context_use_case.execute(files, snippets, rules_obj, user_text, include_tree)
        if result.is_err():
            error: str = result.err() or ""
            QMessageBox.critical(self, "Copy\u00a0Context\u00a0Error", error)

    def _delete_selected(self) -> None:
        self._file_list.delete_selected()

    def _open_settings(self) -> None:
        from codebase_to_llm.domain.rules import Rules

        result_load_rules: Result[Rules, str] = self._rules_repo.load_rules()
        if result_load_rules.is_ok():
            rules_val = result_load_rules.ok()
            assert rules_val is not None
            dialog = RulesManagerDialog(rules_val.to_text(), self._rules_repo)
        else:
            dialog = RulesManagerDialog("", self._rules_repo)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._rules = dialog.text()
            self._refresh_rules_checkboxes()

    def _show_user_request_context_menu(self, pos) -> None:
        menu = QMenu(self)
        copy_context_action = QAction("Copy Context", self)
        copy_context_action.triggered.connect(self._copy_context)  # type: ignore[arg-type]
        menu.addAction(copy_context_action)
        menu.exec_(self.user_request_text_edit.mapToGlobal(pos))

    def _filter_by_name(self, text: str) -> None:
        self._filter_model.setFilterRegularExpression(QRegularExpression(text))
        root_source_idx = self._model.index(str(self._model.rootPath()))
        root_proxy_idx = self._filter_model.mapFromSource(root_source_idx)
        self._tree_view.setRootIndex(root_proxy_idx)

    def _toggle_preview(self, checked: bool) -> None:
        self._preview_panel.setVisible(checked)
        if checked:
            self._toggle_preview_btn.setText("Hide File Preview")
        else:
            self._toggle_preview_btn.setText("Show File Preview")

    def _refresh_rules_checkboxes(self) -> None:
        for i in reversed(range(self._rules_checkbox_layout.count())):
            widget = self._rules_checkbox_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self._include_rules_checkboxes.clear()
        from codebase_to_llm.domain.rules import Rules

        rules_obj = None
        if self._rules:
            rules_result = self._rules_repo.load_rules()
            if rules_result.is_ok():
                rules_obj = rules_result.ok()
        if rules_obj:
            for rule in rules_obj.rules():
                cb = QCheckBox(rule.name())
                cb.setChecked(True)
                cb.setToolTip(rule.description() or "")
                self._rules_checkbox_layout.addWidget(cb)
                self._include_rules_checkboxes[rule.name()] = cb
        else:
            cb = QCheckBox("No Rules Available")
            cb.setEnabled(False)
            self._rules_checkbox_layout.addWidget(cb)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from codebase_to_llm.infrastructure.qt_clipboard_service import QtClipboardService

    root = Path.cwd()
    window = MainWindow(
        repo=FileSystemDirectoryRepository(root),
        clipboard=QtClipboardService(),
        initial_root=root,
        rules_repo=FileSystemRulesRepository(),
        recent_service=RecentRepositoryService(
            FileSystemRecentRepository(Path.home() / ".dcc_recent")
        ),
    )
    window.show()
    sys.exit(app.exec())

