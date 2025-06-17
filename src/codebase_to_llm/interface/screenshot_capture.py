from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Signal, Qt
from PySide6.QtGui import QGuiApplication, QRubberBand, QPixmap
from PySide6.QtWidgets import QWidget


class ScreenSnippetOverlay(QWidget):
    """Transparent overlay to capture a rectangular screen region."""

    captured = Signal(QPixmap)

    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._origin = QPoint()
        self._rubber = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._background = QGuiApplication.primaryScreen().grabWindow(0)

    # ------------------------------------------------------------------ events
    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._origin = event.pos()
        self._rubber.setGeometry(QRect(self._origin, QSize()))
        self._rubber.show()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        rect = QRect(self._origin, event.pos()).normalized()
        self._rubber.setGeometry(rect)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._rubber.hide()
        rect = QRect(self._origin, event.pos()).normalized()
        pixmap = self._background.copy(rect)
        self.captured.emit(pixmap)
        self.close()
