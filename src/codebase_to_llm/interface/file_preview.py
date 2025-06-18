from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Any, Optional

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import (
    QAction,
    QPainter,
    QFontMetrics,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
)
from PySide6.QtWidgets import QPlainTextEdit, QMenu, QTextEdit, QWidget
from pygments import highlight, lex  # type: ignore
from pygments.lexers import PythonLexer, CppLexer, MarkdownLexer  # type: ignore
from pygments.formatter import Formatter  # type: ignore
from pygments.token import Token  # type: ignore


class FileSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language: str):
        super().__init__(document)
        self.language = language
        if language == "python":
            self.lexer = PythonLexer()
        elif language == "cpp":
            self.lexer = CppLexer()
        elif language == "markdown":
            self.lexer = MarkdownLexer()
        else:
            self.lexer = None
        self.formats: dict[Any, QTextCharFormat] = {}
        self._init_formats()

    def _init_formats(self):
        # Basic mapping for a few token types
        def make_format(color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            if italic:
                fmt.setFontItalic(True)
            return fmt

        self.formats = {
            Token.Keyword: make_format("#007020", bold=True),
            Token.Name: make_format("#000000"),
            Token.Comment: make_format("#60a0b0", italic=True),
            Token.String: make_format("#4070a0"),
            Token.Number: make_format("#164", bold=True),
            Token.Operator: make_format("#666666"),
            Token.Punctuation: make_format("#666666"),
            Token.Name.Function: make_format("#06287e", bold=True),
            Token.Name.Class: make_format("#0e84b5", bold=True),
        }

    def highlightBlock(self, text):
        if not self.lexer:
            return
        offset = 0
        for token, value in lex(text, self.lexer):
            length = len(value)
            fmt = self.formats.get(token)
            if fmt:
                self.setFormat(offset, length, fmt)
            offset += length


class FilePreviewWidget(QPlainTextEdit):
    """Read-only file preview widget with line numbers."""

    __slots__ = (
        "_line_number_area",
        "_add_snippet",
        "_current_path",
        "_syntax_highlighter",
    )

    def __init__(self, add_snippet: Callable[[Path, int, int, str], None]):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._add_snippet = add_snippet
        self._current_path: Path | None = None
        self._syntax_highlighter: Optional[FileSyntaxHighlighter] = None

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
            # Syntax highlighting
            ext = path.suffix.lower()
            language = None
            if ext in [".py"]:
                language = "python"
            elif ext in [".cpp", ".cxx", ".cc", ".hpp", ".h", ".c"]:
                language = "cpp"
            elif ext in [".md"]:
                language = "markdown"
            if language:
                self._syntax_highlighter = FileSyntaxHighlighter(
                    self.document(), language
                )
            else:
                self._syntax_highlighter = None
        except Exception as exc:  # pylint: disable=broad-except
            self.setPlainText(f"<Could not preview file: {exc}>")


class _LineNumberArea(QWidget):
    """Thin gutter for line numbers."""

    def __init__(self, editor: FilePreviewWidget) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._editor._paint_line_numbers(event)
