from __future__ import annotations

from pathlib import Path
from typing_extensions import final

from .result import Result, Ok, Err
from .value_object import ValueObject


@final
class SelectedText(ValueObject):
    """Immutable value object representing a snippet from a file."""

    __slots__ = ("path", "start", "end", "text")

    def __init__(self, path: Path, start: int, end: int, text: str) -> None:
        self.path = path
        self.start = start
        self.end = end
        self.text = text

    @classmethod
    def try_create(
        cls, path: Path, start: int, end: int, text: str
    ) -> Result["SelectedText", str]:
        if start < 1 or end < start:
            return Err("Invalid line range")
        return Ok(cls(path, start, end, text))
