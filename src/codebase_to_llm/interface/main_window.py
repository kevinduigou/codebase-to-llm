"""Main application window for the desktop tool."""

from __future__ import annotations

import sys
import webbrowser
import shutil
from pathlib import Path
from typing import Final

from PySide6.QtCore import (
    Qt,
    QDir,
    QSortFilterProxyModel,
    QRegularExpression,
    QSize,
    QMimeData,
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
    QInputDialog,
    QCheckBox,
    QLineEdit,
    QLabel,
)

from codebase_to_llm.application.uc_add_code_snippet_to_context_buffer import (
    AddCodeSnippetToContextBufferUseCase,
)
from codebase_to_llm.application.uc_copy_context import CopyContextUseCase
from codebase_to_llm.application.ports import (
    ClipboardPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    ExternalSourceRepositoryPort,
    RecentRepositoryPort,
    RulesRepositoryPort,
    FavoritePromptsRepositoryPort,
)
from codebase_to_llm.application.uc_add_path_recent_repository_loaded_list import (
    AddPathToRecentRepositoryListUseCase,
)
from codebase_to_llm.application.uc_add_file_to_context_buffer import (
    AddFileToContextBufferUseCase,
)
from codebase_to_llm.application.uc_remove_elmts_from_context_buffer import (
    RemoveElementsFromContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_prompt_from_file import (
    AddPromptFromFileUseCase,
)
from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)
from codebase_to_llm.infrastructure.filesystem_recent_repository import (
    FileSystemRecentRepository,
)

from codebase_to_llm.infrastructure.in_memory_prompt_repository import (
    InMemoryPromptRepository,
)
from codebase_to_llm.infrastructure.url_external_source_repository import (
    UrlExternalSourceRepository,
)
from codebase_to_llm.domain.result import Result

from .context_buffer import ContextBufferWidget
from .file_preview import FilePreviewWidget
from .rules_dialogs import RulesManagerDialog
from .prompts_dialogs import PromptsManagerDialog

from codebase_to_llm.application.uc_add_external_source import (
    AddExternalSourceToContextBufferUseCase,
)
from codebase_to_llm.infrastructure.filesystem_rules_repository import RulesRepository
from codebase_to_llm.infrastructure.in_memory_context_buffer_repository import (
    InMemoryContextBufferRepository,
)
from codebase_to_llm.application.ports import PromptRepositoryPort
from codebase_to_llm.application.uc_set_prompt_from_favorite import (
    AddPromptFromFavoriteLisUseCase,
)

class DragDropFileSystemModel(QFileSystemModel):
    """Custom file system model that supports drag and drop operations."""
    
    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction

    def canDropMimeData(self, data, action, row, column, parent):
        if not data.hasUrls():
            return False
        return True

    def dropMimeData(self, data, action, row, column, parent):
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        if action == Qt.IgnoreAction:
            return True

        target_dir = self.filePath(parent)
        if not Path(target_dir).is_dir():
            target_dir = str(Path(target_dir).parent)

        for url in data.urls():
            source_path = url.toLocalFile()
            file_name = Path(source_path).name
            target_path = str(Path(target_dir) / file_name)

            # Prevent overwriting
            if Path(target_path).exists():
                QMessageBox.warning(None, "Warning", f"{file_name} already exists in target directory.")
                continue

            try:
                if action == Qt.MoveAction:
                    shutil.move(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)
            except Exception as e:
                QMessageBox.critical(None, "Error", str(e))
                return False

        return True

class RulesMenu(QMenu):
    """A QMenu that does not close when a checkable action is toggled (for rules toggling)."""

    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.pos())
        if action and action.isCheckable():
            # Toggle the action manually
            action.setChecked(not action.isChecked())
            # Emit the triggered signal manually (no arguments)
            action.triggered.emit()
            # Do NOT call super().mouseReleaseEvent(event) to prevent menu from closing
            return
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    """Qt main window binding infrastructure to application layer."""

    __slots__ = (
        "_tree_view",
        "_file_preview",
        "_model",
        "_repo",
        "_clipboard",
        "_copy_context_use_case",
        "_recent_repo",
        "_rules_repo",
        "_recent_menu",
        "user_request_text_edit",
        "_include_rules_checkboxes",
        "include_project_structure_checkbox",
        "_filter_model",
        "_name_filter_edit",
        "_toggle_preview_btn",
        "_preview_panel",
        "_rules_checkbox_container",
        "_rules_checkbox_layout",
        "_include_rules_actions",
        "_rules_menu",
        "_rules_button",
        "_context_buffer",
        "_prompt_repo",
        "_add_prompt_from_file_use_case",
        "_add_prompt_from_favorite_list_use_case",
    )

    def __init__(
        self,
        repo: DirectoryRepositoryPort,
        clipboard: ClipboardPort,
        initial_root: Path,
        rules_repo: RulesRepositoryPort,
        prompts_repo: FavoritePromptsRepositoryPort,
        recent_repo: RecentRepositoryPort,
        external_repo: ExternalSourceRepositoryPort,
        context_buffer: ContextBufferPort,
        prompt_repo: PromptRepositoryPort,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Desktop Context Copier")
        self.resize(1200, 700)

        self._repo = repo
        self._clipboard: Final = clipboard
        self._rules_repo = rules_repo
        self._prompts_repo = prompts_repo
        self._recent_repo = recent_repo
        self._context_buffer = context_buffer
        self._external_repo = external_repo
        self._prompt_repo = prompt_repo

        # Use cases Initialization
        self._copy_context_use_case = CopyContextUseCase(
            self._context_buffer, self._rules_repo, self._repo, self._clipboard
        )
        self._add_path_recent_repository_loaded_list_use_case = (
            AddPathToRecentRepositoryListUseCase()
        )
        self._add_external_source_use_case = AddExternalSourceToContextBufferUseCase(
            self._context_buffer, self._external_repo
        )
        self._add_file_to_context_buffer = AddFileToContextBufferUseCase(
            self._context_buffer
        )
        self._add_code_snippet_to_context_buffer = AddCodeSnippetToContextBufferUseCase(
            self._context_buffer
        )
        self._remove_elmts_from_contxt_buffer = RemoveElementsFromContextBufferUseCase(
            self._context_buffer
        )
        self._add_prompt_from_file_use_case = AddPromptFromFileUseCase(
            self._prompt_repo
        )
        self._add_prompt_from_favorite_list_use_case = AddPromptFromFavoriteLisUseCase(
            self._prompt_repo
        )

        splitter = QSplitter(Qt.Horizontal, self)  # type: ignore[attr-defined]
        splitter.setChildrenCollapsible(False)

        # --------------------------- left — directory tree
        self._model = DragDropFileSystemModel()
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
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDragDropMode(QTreeView.DragDrop)
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

        title_bar_layout = QHBoxLayout()
        title_bar_layout.addWidget(buffer_title)
        title_bar_layout.addStretch(1)
        right_layout.addLayout(title_bar_layout)

        self._context_buffer_widget = ContextBufferWidget(
            initial_root,
            lambda: self._handle_copy_context_widget(),
            self._add_file_to_context_buffer,
            self._remove_elmts_from_contxt_buffer,
            self._add_external_source_use_case,
            self._add_code_snippet_to_context_buffer,
        )
        right_layout.addWidget(self._context_buffer_widget)

        splitter.addWidget(right_panel)

        # --------------------------- middle — file preview
        self._file_preview = FilePreviewWidget(self._context_buffer_widget.add_snippet)
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
        # Create a vertical splitter to allow resizing between main content and user request text edit
        vertical_splitter = QSplitter(Qt.Orientation.Vertical, self)
        vertical_splitter.setChildrenCollapsible(False)
        vertical_splitter.addWidget(splitter)
        self.user_request_text_edit = QPlainTextEdit()
        self.user_request_text_edit.setPlaceholderText(
            "Describe your need or the bug here, LLM User Request..."
        )
        # Remove fixed height to allow resizing
        # self.user_request_text_edit.setFixedHeight(100)
        vertical_splitter.addWidget(self.user_request_text_edit)
        # Set initial sizes: main content larger, text edit smaller
        vertical_splitter.setStretchFactor(0, 5)
        vertical_splitter.setStretchFactor(1, 1)
        layout.addWidget(vertical_splitter)
        self.setCentralWidget(central)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        choose_dir_icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_DirOpenIcon
        )
        choose_dir_button = QToolButton(self)
        choose_dir_button.setIcon(choose_dir_icon)
        choose_dir_button.setText("Choose Directory")
        choose_dir_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        choose_dir_button.clicked.connect(self._choose_directory)
        toolbar.addWidget(choose_dir_button)

        self._recent_menu = QMenu(self)
        recent_button = QToolButton(self)
        recent_icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_DirHomeIcon
        )

        recent_button.setIcon(recent_icon)
        recent_button.setText("Recently Used")
        recent_button.setMenu(self._recent_menu)
        recent_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        recent_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.addWidget(recent_button)
        self._populate_recent_menu()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        settings_icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogDetailedView
        )
        settings_menu = QMenu(self)
        edit_rules_action = QAction("Edit Rules", self)
        edit_rules_action.triggered.connect(self._open_settings)  # type: ignore[arg-type]
        settings_menu.addAction(edit_rules_action)
        edit_prompts_action = QAction("Edit Favorite Prompts", self)
        edit_prompts_action.triggered.connect(self._open_prompts_settings)  # type: ignore[arg-type]
        settings_menu.addAction(edit_prompts_action)
        settings_button = QToolButton(self)
        settings_button.setIcon(settings_icon)
        settings_button.setMenu(settings_menu)
        settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        settings_button.setToolTip("Settings")
        toolbar.addWidget(settings_button)

        bottom_bar_layout = QHBoxLayout()
        self.include_project_structure_checkbox = QCheckBox("Include Project Structure")
        self.include_project_structure_checkbox.setChecked(True)
        self._include_rules_actions: dict[str, QAction] = {}
        self._rules_menu = RulesMenu(self)
        self._rules_button = QToolButton(self)
        self._rules_button.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton)
        )
        self._rules_button.setText("Rules")
        self._rules_button.setMenu(self._rules_menu)
        self._rules_button.setMinimumHeight(30)
        self._rules_button.setIconSize(QSize(24, 24))
        self._rules_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._rules_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._refresh_rules_checkboxes()
        bottom_bar_layout.addWidget(self.include_project_structure_checkbox)
        bottom_bar_layout.addWidget(self._rules_button)
        bottom_bar_layout.addStretch(1)

        copy_icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_DialogApplyButton
        )
        copy_btn = QPushButton("Copy Context")
        copy_btn.setIcon(copy_icon)
        copy_btn.setIconSize(QSize(24, 24))
        copy_btn.setMinimumHeight(30)
        copy_btn.clicked.connect(self._copy_context)  # type: ignore[arg-type]

        external_icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogNewFolder
        )
        external_btn = QPushButton("Add External Source")
        external_btn.setIcon(external_icon)
        external_btn.setIconSize(QSize(24, 24))
        external_btn.setMinimumHeight(30)
        external_btn.clicked.connect(self._prompt_external_source)  # type: ignore[arg-type]

        goto_menu = QMenu(self)
        goto_btn = QToolButton(self)
        goto_btn.setText("Go To")
        goto_btn.setMenu(goto_menu)
        goto_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        goto_btn.setMinimumHeight(30)

        chatgpt_action = QAction("ChatGPT", self)
        chatgpt_action.triggered.connect(self._open_chatgpt)  # type: ignore[arg-type]
        goto_menu.addAction(chatgpt_action)

        claude_action = QAction("Claude", self)
        claude_action.triggered.connect(self._open_claude)  # type: ignore[arg-type]
        goto_menu.addAction(claude_action)

        bottom_bar_layout.addWidget(external_btn)
        bottom_bar_layout.addWidget(copy_btn)
        bottom_bar_layout.addWidget(goto_btn)

        layout.addLayout(bottom_bar_layout)

        self.user_request_text_edit.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
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
            # Show menu for creating new items when clicking empty space
            menu = QMenu(self)
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self._create_item(index, False))
            new_folder_action = QAction("New Folder", self)
            new_folder_action.triggered.connect(lambda: self._create_item(index, True))
            menu.addAction(new_file_action)
            menu.addAction(new_folder_action)
            menu.exec_(self._tree_view.viewport().mapToGlobal(pos))
            return

        source_index = self._filter_model.mapToSource(index)
        file_path = Path(self._model.filePath(source_index))
        
        menu = QMenu(self)
        
        # Add file management actions
        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(lambda: self._create_item(index, False))
        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(lambda: self._create_item(index, True))
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_item(index))
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_item(index))
        
        menu.addAction(new_file_action)
        menu.addAction(new_folder_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()

        # Add existing actions if it's a file
        if file_path.is_file():
            preview_action = QAction("Open Preview", self)
            preview_action.triggered.connect(
                lambda checked=False, p=file_path: self._file_preview.load_file(p)
            )
            menu.addAction(preview_action)
            prompt_action = QAction("Add as Prompt", self)
            prompt_action.triggered.connect(
                lambda checked=False, p=file_path: self._add_prompt_from_file(p)
            )
            menu.addAction(prompt_action)
            add_action = QAction("Add to Context Buffer", self)
            add_action.triggered.connect(
                lambda checked=False, p=file_path: self._context_buffer_widget.add_file(p)
            )
            menu.addAction(add_action)

        menu.exec_(self._tree_view.viewport().mapToGlobal(pos))

    def _create_item(self, parent_index, is_folder: bool) -> None:
        # Get the parent directory path
        if parent_index.isValid():
            source_index = self._filter_model.mapToSource(parent_index)
            parent_path = Path(self._model.filePath(source_index))
            if parent_path.is_file():
                parent_path = parent_path.parent
        else:
            parent_path = Path(self._model.rootPath())

        # Get the new item name from user
        item_type = "folder" if is_folder else "file"
        name, ok = QInputDialog.getText(self, f"Create {item_type}", "Enter name:")
        if not ok or not name:
            return

        try:
            new_path = parent_path / name
            if is_folder:
                new_path.mkdir(exist_ok=False)
            else:
                new_path.touch(exist_ok=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _delete_item(self, index) -> None:
        if not index.isValid():
            return

        source_index = self._filter_model.mapToSource(index)
        path = Path(self._model.filePath(source_index))
        
        # Confirm deletion
        msg = f"Are you sure you want to delete '{path.name}'?"
        if path.is_dir():
            msg += "\nThis will delete the folder and all its contents!"
            
        reply = QMessageBox.question(self, 'Confirm Delete', msg, 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _rename_item(self, index) -> None:
        if not index.isValid():
            return

        source_index = self._filter_model.mapToSource(index)
        old_path = Path(self._model.filePath(source_index))
        
        # Get new name from user
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter new name:", text=old_path.name
        )
        
        if ok and new_name and new_name != old_path.name:
            try:
                new_path = old_path.parent / new_name
                old_path.rename(new_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _add_prompt_from_file(self, path: Path) -> None:
        result = self._add_prompt_from_file_use_case.execute(path)
        if result.is_err():
            QMessageBox.warning(self, "Prompt Error", result.err() or "")
            return
        prompt = result.ok()
        if prompt is None:
            return
        self.user_request_text_edit.setPlainText(prompt.content)

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
            self._copy_context_use_case = CopyContextUseCase(
                self._context_buffer, self._rules_repo, self._repo, self._clipboard
            )
            self._context_buffer_widget.clear()
            self._context_buffer_widget.set_root_path(path)
            self._file_preview.clear()
            # Save to recent repo
            result = self._recent_repo.load_paths()
            paths: list[Path] = result.ok() or []
            if path not in paths:
                paths.append(path)
                self._recent_repo.save_paths(paths)
            self._populate_recent_menu()

    def _open_recent(self, path: Path) -> None:
        self._model.setRootPath(str(path))
        self._filter_model.invalidateFilter()
        self._tree_view.setRootIndex(
            self._filter_model.mapFromSource(self._model.index(str(path)))
        )
        self._repo = FileSystemDirectoryRepository(path)  # type: ignore[assignment]
        self._copy_context_use_case = CopyContextUseCase(
            self._context_buffer, self._rules_repo, self._repo, self._clipboard
        )
        self._context_buffer_widget.clear()
        self._context_buffer_widget.set_root_path(path)
        self._file_preview.clear()
        # Save to recent repo
        result = self._recent_repo.load_paths()
        paths: list[Path] = result.ok() or []
        if path not in paths:
            paths.append(path)
            self._recent_repo.save_paths(paths)
        self._populate_recent_menu()

    def _populate_recent_menu(self) -> None:
        self._recent_menu.clear()
        result = self._recent_repo.load_paths()
        if result.is_err():
            return
        paths = result.ok() or []
        for path in paths:
            action = QAction(str(path), self)
            action.triggered.connect(lambda checked=False, p=path: self._open_recent(p))  # type: ignore[arg-type]
            self._recent_menu.addAction(action)

    def _copy_context(self) -> None:  # noqa: D401
        result = self._copy_context_use_case.execute(
            self.user_request_text_edit.toPlainText(),
            self.include_project_structure_checkbox.isChecked(),
            self._model.rootPath(),
        )
        if result.is_err():
            error: str = result.err() or ""
            QMessageBox.critical(self, "Copy Context Error", error)

    def _prompt_external_source(self) -> None:
        url, ok = QInputDialog.getText(
            self,
            "Add External Source",
            "Enter web page or YouTube URL:",
        )
        if not ok or not url.strip():
            return

        result = self._context_buffer_widget.add_external_source(url.strip())

        # Update the graphical model

        if result.is_err():
            QMessageBox.warning(
                self,
                "Load Error",
                result.err() or "Could not load external source.",
            )

    def _open_settings(self) -> None:
        from codebase_to_llm.domain.rules import Rules

        result_load_rules: Result[Rules, str] = self._rules_repo.load_rules()
        if result_load_rules.is_ok():
            rules_val = result_load_rules.ok()
            assert rules_val is not None
            # Only pass if self._rules_repo is a RulesRepository, else skip
            from codebase_to_llm.infrastructure.filesystem_rules_repository import (
                RulesRepository,
            )

            if isinstance(self._rules_repo, RulesRepository):
                dialog = RulesManagerDialog(rules_val.to_text(), self._rules_repo)
            else:
                dialog = RulesManagerDialog(rules_val.to_text(), RulesRepository())
        else:
            from codebase_to_llm.infrastructure.filesystem_rules_repository import (
                RulesRepository,
            )

            if isinstance(self._rules_repo, RulesRepository):
                dialog = RulesManagerDialog("", self._rules_repo)
            else:
                dialog = RulesManagerDialog("", RulesRepository())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_rules_checkboxes()

    def _open_prompts_settings(self) -> None:
        result = self._prompts_repo.load_prompts()
        from codebase_to_llm.infrastructure.filesystem_favorite_prompts_repository import (
            FavoritePromptsRepository,
        )

        if result.is_ok():
            prompts_val = result.ok()
            assert prompts_val is not None
            if isinstance(self._prompts_repo, FavoritePromptsRepository):
                dialog = PromptsManagerDialog(self._prompts_repo)
            else:
                dialog = PromptsManagerDialog(FavoritePromptsRepository())
        else:
            if isinstance(self._prompts_repo, FavoritePromptsRepository):
                dialog = PromptsManagerDialog(self._prompts_repo)
            else:
                dialog = PromptsManagerDialog(FavoritePromptsRepository())
        dialog.exec()

    def _show_user_request_context_menu(self, pos) -> None:
        menu = QMenu(self)
        copy_context_action = QAction("Copy Context", self)
        copy_context_action.triggered.connect(self._copy_context)  # type: ignore[arg-type]
        menu.addAction(copy_context_action)

        prompts_result = self._prompts_repo.load_prompts()
        if prompts_result.is_ok():
            prompts_obj = prompts_result.ok()
            assert prompts_obj is not None
            if prompts_obj.prompts():
                menu.addSeparator()
                for prompt in prompts_obj.prompts():
                    action = QAction(prompt.name(), self)

                    def make_triggered_action(content):
                        return (
                            lambda checked=False: self._handle_set_prompt_from_favorite(
                                content
                            )
                        )

                    action.triggered.connect(make_triggered_action(prompt.content()))
                    menu.addAction(action)

        menu.exec_(self.user_request_text_edit.mapToGlobal(pos))

    def _handle_set_prompt_from_favorite(self, content: str) -> None:
        result = self._add_prompt_from_favorite_list_use_case.execute(content)
        if result.is_err():
            QMessageBox.warning(
                self, "Prompt Error", result.err() or "Could not set prompt."
            )
        else:
            self.user_request_text_edit.setPlainText(content)

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
        self._rules_menu.clear()
        self._include_rules_actions.clear()

        rules_obj = None
        if self._rules_repo:
            rules_result = self._rules_repo.load_rules()
            if rules_result.is_ok():
                rules_obj = rules_result.ok()
        if rules_obj:
            for rule in rules_obj.rules():
                action = QAction(rule.name(), self)
                action.setCheckable(True)
                action.setChecked(rule.enabled())
                action.setToolTip(rule.description() or "")

                action.triggered.connect(
                    lambda checked=False, rule=rule: self._rules_repo.update_rule_enabled(
                        rule.name(), checked
                    )
                )
                self._rules_menu.addAction(action)
                self._include_rules_actions[rule.name()] = action
        else:
            action = QAction("No Rules Available", self)
            action.setEnabled(False)
            self._rules_menu.addAction(action)

    def _handle_copy_context_widget(self) -> None:
        result = self._copy_context_use_case.execute(
            self.user_request_text_edit.toPlainText(),
            self.include_project_structure_checkbox.isChecked(),
            self._model.rootPath(),
        )
        if result.is_err():
            error: str = result.err() or ""
            QMessageBox.critical(self, "Copy Context Error", error)

    def _open_chatgpt(self) -> None:
        """Copy context then open ChatGPT in the browser."""
        self._copy_context()
        webbrowser.open("https://chat.openai.com/")

    def _open_claude(self) -> None:
        """Copy context then open Claude in the browser."""
        self._copy_context()
        webbrowser.open("https://claude.ai/")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from codebase_to_llm.infrastructure.qt_clipboard_service import QtClipboardService
    from codebase_to_llm.infrastructure.filesystem_favorite_prompts_repository import (
        FavoritePromptsRepository,
    )

    root = Path.cwd()
    window = MainWindow(
        repo=FileSystemDirectoryRepository(root),
        clipboard=QtClipboardService(),
        initial_root=root,
        rules_repo=RulesRepository(),
        prompts_repo=FavoritePromptsRepository(),
        recent_repo=FileSystemRecentRepository(Path.home() / ".dcc_recent"),
        external_repo=UrlExternalSourceRepository(),
        context_buffer=InMemoryContextBufferRepository(),
        prompt_repo=InMemoryPromptRepository(),
    )
    window.show()
    sys.exit(app.exec())
