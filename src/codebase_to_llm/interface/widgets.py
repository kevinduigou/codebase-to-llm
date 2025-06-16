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


class _LineNumberArea(QWidget):
    """Thin gutter for line numbers."""

    def __init__(self, editor: "_FilePreviewWidget") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._editor._paint_line_numbers(event)


class _FileListWidget(QListWidget):
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


class _FilePreviewWidget(QPlainTextEdit):
    """Read-only file preview widget with line numbers."""

    __slots__ = ("_line_number_area", "_add_snippet", "_current_path")

    def __init__(self, add_snippet: Callable[[Path, int, int, str], None]):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._add_snippet = add_snippet
        self._current_path: Path | None = None

        self._line_number_area = _LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)  # type: ignore[arg-type]
        self.updateRequest.connect(self._update_line_number_area)  # type: ignore[arg-type]
        self.cursorPositionChanged.connect(self._highlight_current_line)  # type: ignore[arg-type]

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _line_number_area_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        fm = QFontMetrics(self.font())
        return 4 + fm.horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )

    def _paint_line_numbers(self, event) -> None:
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
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            return
        selection = QTextEdit.ExtraSelection()  # type: ignore[attr-defined]
        line_color = self.palette().alternateBase().color().lighter(120)
        selection.format.setBackground(line_color)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def _show_context_menu(self, pos) -> None:
        if not self.textCursor().hasSelection():
            return
        menu = QMenu(self)
        copy_action = QAction("Copy Selected", self)
        copy_action.triggered.connect(self.copy)  # type: ignore[arg-type]
        menu.addAction(copy_action)
        add_action = QAction("Add to Context Buffer", self)
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
