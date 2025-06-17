from __future__ import annotations

from typing_extensions import final

from .result import Result, Ok, Err
from .value_object import ValueObject


@final
class Screenshot(ValueObject):
    """Immutable screenshot captured as base64 data."""

    __slots__ = ("_description", "_data")

    _description: str
    _data: str

    @staticmethod
    def try_create(description: str, data_base64: str) -> Result["Screenshot", str]:
        desc = description.strip() or "screenshot"
        data = data_base64.strip()
        if not data:
            return Err("Image data cannot be empty")
        return Ok(Screenshot(desc, data))

    def __init__(self, description: str, data_base64: str) -> None:
        self._description = description
        self._data = data_base64

    def description(self) -> str:
        return self._description

    def data(self) -> str:
        return self._data
