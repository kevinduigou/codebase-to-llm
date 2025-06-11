from __future__ import annotations

from typing_extensions import final

from domain.value_object import ValueObject

from .result import Result, Ok, Err


class Rules(ValueObject):
    """
    Immutable wrapper around the raw rules text.

    Construction goes through ``try_create`` so that illegal
    states (empty text) are unrepresentable.
    """

    __slots__ = ("_text",)
    _text: str

    # ----------------------------------------------------------------- factory
    @staticmethod
    def try_create(text: str) -> Result["Rules", str]:
        trimmed = text.strip()
        return Err("Rules text cannot be empty.") if not trimmed else Ok(Rules(trimmed))

    # ----------------------------------------------------------------- ctor (kept private – do not call directly)
    def __init__(self, text: str):
        self._text = text

    # ----------------------------------------------------------------- accessors
    def text(self) -> str:  # noqa: D401
        return self._text
