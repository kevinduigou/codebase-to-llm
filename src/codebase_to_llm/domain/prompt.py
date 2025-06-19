from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import final

from .value_object import ValueObject
from .result import Result, Ok, Err


@final
@dataclass(frozen=True)
class Prompt(ValueObject):
    """Value object representing a user prompt."""

    content: str

    @staticmethod
    def try_create(content: str) -> Result["Prompt", str]:
        if not content or not content.strip():
            return Err("Prompt cannot be empty")
        return Ok(Prompt(content))
