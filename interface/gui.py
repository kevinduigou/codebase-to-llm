from __future__ import annotations

import sys
from pathlib import Path
from typing import Final, List, Callable
import os
import re

from PySide6.QtCore import (
    Qt,
    QMimeData,
    QUrl,
    QDir,
    QSortFilterProxyModel,
    QRegularExpression,
    QRect,
    QSize,
)
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDropEvent,
    QDragMoveEvent,
    QPainter,
    QFontMetrics,
)
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
    QLabel,
)

from application.copy_context import CopyContextUseCase
from application.ports import (
    ClipboardPort,
    DirectoryRepositoryPort,
)
from application.rules_service import RulesService
from application.recent_repository_service import RecentRepositoryService
from infrastructure.filesystem_recent_repository import FileSystemRecentRepository
from infrastructure.filesystem_rules_repository import FileSystemRulesRepository
from domain.result import Err, Result
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from domain.directory_tree import should_ignore, get_ignore_tokens
from domain.selected_text import SelectedText


class _LineNumberArea(QWidget):
    """Thin gutter that the parent editor paints line numbers into."""

    def __init__(self, editor: " _FilePreviewWidget"):  # editor is the parent
        super().__init__(editor)
        self._editor = editor

    # Width is dictated by the editor's calculation
    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event):  # noqa: N802
        self._editor._paint_line_numbers(event)


class _FileListWidget(QListWidget):
    """Right-panel list accepting drops from the tree view."""

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

    def add_snippet(self, path: Path, start: int, end: int, text: str) -> None:
        try:
            rel_path = path.relative_to(self._root_path)
        except ValueError:
            rel_path = path
        label = f"{rel_path}:{start}:{end}"
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, text)
        self.addItem(item)

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


class _FilePreviewWidget(QPlainTextEdit):
    """Middle-panel read-only file preview widget with a line-number gutter."""

    __slots__ = ("_line_number_area", "_add_snippet", "_current_path")

    def __init__(self, add_snippet: Callable[[Path, int, int, str], None]):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._add_snippet = add_snippet
        self._current_path: Path | None = None

        # Line-number gutter setup
        self._line_number_area = _LineNumberArea(self)

        # Keep gutter in sync with the document
        self.blockCountChanged.connect(self._update_line_number_area_width)  # type: ignore[arg-type]
        self.updateRequest.connect(self._update_line_number_area)  # type: ignore[arg-type]
        self.cursorPositionChanged.connect(self._highlight_current_line)  # type: ignore[arg-type]

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Context-menu for copying selected text
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    # ────────────────────────────── Line-number logic ────────────────────────
    def _line_number_area_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))  # at least 3 chars
        fm = QFontMetrics(self.font())
        return 4 + fm.horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):  # slot
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):  # slot
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )

    def _paint_line_numbers(self, event):  # called from _LineNumberArea.paintEvent
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self.palette().window().color())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())
        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 4,
                    height,
                    Qt.AlignRight | Qt.AlignVCenter,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _highlight_current_line(self):  # slot
        extra_selections = []
        if not self.isReadOnly():
            return
        selection = QTextEdit.ExtraSelection()  # type: ignore[attr-defined]
        line_color = self.palette().alternateBase().color().lighter(120)
        selection.format.setBackground(line_color)
        # selection.format.setProperty(QTextEdit.ExtraSelection.FullWidthSelection, True)  # type: ignore[attr-defined]
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    # ───────────────────────────── context menu (unchanged) ──────────────────
    def _show_context_menu(self, pos) -> None:
        if not self.textCursor().hasSelection():
            return
        menu = QMenu(self)
        copy_action = QAction("Copy Selected", self)
        copy_action.triggered.connect(self.copy)  # type: ignore[arg-type]
        menu.addAction(copy_action)
        add_action = QAction("Add to Content Buffer", self)
        add_action.triggered.connect(self._handle_add_to_buffer)  # type: ignore[arg-type]
        menu.addAction(add_action)
        menu.exec_(self.mapToGlobal(pos))

    def _handle_add_to_buffer(self) -> None:
        if self._current_path is None:
            return
        cursor = self.textCursor()
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()
        doc = self.document()
        start_line = doc.findBlock(start_pos).blockNumber() + 1
        end_line = doc.findBlock(end_pos).blockNumber() + 1
        text = cursor.selectedText().replace("\u2029", os.linesep)
        self._add_snippet(self._current_path, start_line, end_line, text)

    # ───────────────────────────── load_file helper (unchanged) ──────────────
    def load_file(self, path: Path, max_bytes: int = 200_000) -> None:
        try:
            with path.open("rb") as f:
                data = f.read(max_bytes)
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = data.decode("latin-1", errors="replace")
            self.setPlainText(text)
            self._current_path = path
        except Exception as exc:  # pylint: disable=broad-except
            self.setPlainText(f"<Could not preview file: {exc}>")


class RulesDialog(QDialog):
    """Simple dialog to edit rules."""

    __slots__ = ("_edit", "_rules_service")

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
        "_file_preview",
        "_file_list",
        "_model",
        "_repo",
        "_clipboard",
        "_copy_context_use_case",
        "_recent_service",
        "_rules_service",
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
        self.resize(1200, 700)

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
        self._filter_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
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

        # Add title for directory tree
        tree_title = QLabel("Directory Tree")
        tree_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        tree_title.setToolTip(
            "Browse and navigate through your project's directory structure. Drag files to the right panel to include them in the context."
        )
        left_layout.addWidget(tree_title)

        left_layout.addWidget(self._name_filter_edit)
        left_layout.addWidget(self._tree_view)

        splitter.addWidget(left_panel)

        # --------------------------- right — dropped files list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Add title for content buffer
        buffer_title = QLabel("Content Buffer")
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

        # Add title for file preview
        preview_title = QLabel("File Preview")
        preview_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        preview_title.setToolTip(
            "View and select text from files. Double-click files in the directory tree to preview them here. Selected text can be added to the context buffer."
        )
        preview_layout.addWidget(preview_title)

        preview_layout.addWidget(self._file_preview)
        splitter.addWidget(self._preview_panel)
        self._preview_panel.setVisible(False)

        # Set initial splitter sizes
        splitter.setStretchFactor(0, 2)  # Left tree
        splitter.setStretchFactor(1, 3)  # Preview
        splitter.setStretchFactor(2, 2)  # Right list

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

        # Toggle button for preview panel visibility
        self._toggle_preview_btn = QToolButton(self)
        self._toggle_preview_btn.setText("Hide File Preview")
        self._toggle_preview_btn.setCheckable(True)
        self._toggle_preview_btn.setChecked(False)
        self._toggle_preview_btn.toggled.connect(self._toggle_preview)
        toolbar.addWidget(self._toggle_preview_btn)

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

        # --------------------------- connections for preview
        # Show preview only on double click
        self._tree_view.doubleClicked.connect(
            self._handle_tree_double_click
        )  # type: ignore[arg-type]

    # ──────────────────────────────────────────────────────────────────

    # ----------------------------- Preview logic
    def _handle_tree_double_click(self, proxy_index):  # noqa: D401 (simple verb)
        source_index = self._filter_model.mapToSource(proxy_index)
        file_path = Path(self._model.filePath(source_index))
        if file_path.is_file():
            self._file_preview.load_file(file_path)
            self._preview_panel.setVisible(True)
            if hasattr(self, "_toggle_preview_btn"):
                self._toggle_preview_btn.setChecked(True)
        else:
            self._file_preview.clear()

    # ----------------------------- Existing methods (unchanged except splitter adjustments)

    def _choose_directory(self):  # noqa: D401 (simple verb)
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            path = Path(directory)
            self._model.setRootPath(str(path))
            self._filter_model.invalidateFilter()
            self._tree_view.setRootIndex(
                self._filter_model.mapFromSource(self._model.index(str(path)))
            )
            # Re-initialise repository for new root
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
            action.triggered.connect(
                lambda checked=False, p=path: self._open_recent(p)
            )  # type: ignore[arg-type]
            self._recent_menu.addAction(action)

    def _copy_context(self):  # noqa: D401 (simple verb)
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
                    snippet_result = SelectedText.try_create(
                        Path(path_str), int(start_str), int(end_str), text_data
                    )
                    if snippet_result.is_ok():
                        snippets.append(snippet_result.ok())
                except Exception:
                    continue
            else:
                files.append(Path(item.text()))
        user_text = self.user_request_text_edit.toPlainText().strip()
        rules_text = self._rules if self._include_rules_checkbox.isChecked() else None
        include_tree = self._include_tree_checkbox.isChecked()
        result = self._copy_context_use_case.execute(
            files, snippets, rules_text, user_text, include_tree
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
        # Apply (or clear) the regex
        self._filter_model.setFilterRegularExpression(QRegularExpression(text))

        # Always reset the root index so the view stays anchored
        root_source_idx = self._model.index(str(self._model.rootPath()))
        root_proxy_idx = self._filter_model.mapFromSource(root_source_idx)
        self._tree_view.setRootIndex(root_proxy_idx)

    def _toggle_preview(self, checked: bool) -> None:
        """Show or hide the file preview panel."""
        self._preview_panel.setVisible(checked)


# Optional: add a small demo runner when executed directly
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Replace these with actual implementations in your project context
    from infrastructure.qt_clipboard_service import QtClipboardService

    root = Path.cwd()
    window = MainWindow(
        repo=FileSystemDirectoryRepository(root),
        clipboard=QtClipboardService(),
        initial_root=root,
        rules_service=RulesService(FileSystemRulesRepository()),
        recent_service=RecentRepositoryService(
            FileSystemRecentRepository(Path.home() / ".dcc_recent")
        ),
    )
    window.show()
    sys.exit(app.exec())
