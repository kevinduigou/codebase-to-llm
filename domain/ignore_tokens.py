from __future__ import annotations

from typing import Iterable, Tuple
from typing_extensions import final

from .value_object import ValueObject
from .result import Result, Ok, Err


@final
class IgnoreTokens(ValueObject):
    """Immutable list of ignore tokens."""

    __slots__ = ("_tokens",)
    _tokens: Tuple[str, ...]

    # ----------------------------------------------------------------- factory
    @staticmethod
    def try_create(tokens: Iterable[str]) -> Result["IgnoreTokens", str]:
        unique: list[str] = []
        for token in tokens:
            trimmed = token.strip()
            if trimmed and trimmed not in unique:
                unique.append(trimmed)
        return Ok(IgnoreTokens(tuple(unique)))

    # ----------------------------------------------------------------- ctor
    def __init__(self, tokens: Tuple[str, ...]):
        self._tokens = tokens

    # ----------------------------------------------------------------- accessor
    def tokens(self) -> Tuple[str, ...]:  # noqa: D401
        return self._tokens
