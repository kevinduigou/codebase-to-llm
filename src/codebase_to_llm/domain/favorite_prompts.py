from __future__ import annotations

from typing import Iterable, Tuple
from typing_extensions import final

from .value_object import ValueObject
from .result import Result, Ok, Err


@final
class FavoritePrompt:
    """Single favorite prompt with a mandatory name and text."""

    __slots__ = ("_name", "_content")

    @staticmethod
    def try_create(name: str, content: str) -> Result["FavoritePrompt", str]:
        trimmed_name = name.strip()
        if not trimmed_name:
            return Err("Prompt name cannot be empty.")
        return Ok(FavoritePrompt(trimmed_name, content))

    def __init__(self, name: str, content: str) -> None:
        self._name = name
        self._content = content

    def name(self) -> str:
        return self._name

    def content(self) -> str:
        return self._content


@final
class FavoritePrompts(ValueObject):
    """Immutable collection of :class:`FavoritePrompt` objects."""

    __slots__ = ("_prompts",)
    _prompts: Tuple[FavoritePrompt, ...]

    @staticmethod
    def try_create(prompts: Iterable[FavoritePrompt]) -> Result["FavoritePrompts", str]:
        return Ok(FavoritePrompts(tuple(prompts)))

    def __init__(self, prompts: Tuple[FavoritePrompt, ...]):
        self._prompts = prompts

    def prompts(self) -> Tuple[FavoritePrompt, ...]:  # noqa: D401
        return self._prompts

    def remove_prompt(self, name: str) -> "FavoritePrompts":
        new_prompts = tuple(p for p in self._prompts if p.name() != name)
        return FavoritePrompts(new_prompts)

