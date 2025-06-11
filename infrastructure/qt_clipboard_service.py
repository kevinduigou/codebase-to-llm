from __future__ import annotations

from PySide6.QtGui import QGuiApplication

from application.ports import ClipboardPort


class QtClipboardService(ClipboardPort):
    """Thin wrapper over Qt clipboard to honour the ClipboardPort interface."""

    __slots__ = ()

    def set_text(self, text: str) -> None:  # noqa: D401 (simple verb)
        QGuiApplication.clipboard().setText(text)