from __future__ import annotations

from typing import Iterable, Tuple
from typing_extensions import final

from .value_object import ValueObject
from .result import Result, Ok, Err


@final
class FavoritePromptId(ValueObject):
    """Unique identifier for a favorite prompt."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["FavoritePromptId", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Favorite prompt id cannot be empty.")
        return Ok(FavoritePromptId(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class FavoritePrompt:
    """Single favorite prompt with a mandatory id, name and text."""

    __slots__ = ("_id", "_name", "_content")

    @staticmethod
    def try_create(
        id_value: str, name: str, content: str
    ) -> Result["FavoritePrompt", str]:
        id_result = FavoritePromptId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid id")
        trimmed_name = name.strip()
        if not trimmed_name:
            return Err("Prompt name cannot be empty.")
        id_obj = id_result.ok()
        assert id_obj is not None
        return Ok(FavoritePrompt(id_obj, trimmed_name, content))

    def __init__(self, id: FavoritePromptId, name: str, content: str) -> None:
        self._id = id
        self._name = name
        self._content = content

    def id(self) -> FavoritePromptId:
        return self._id

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

    def add_prompt(self, prompt: FavoritePrompt) -> Result["FavoritePrompts", str]:
        for existing in self._prompts:
            if existing.id().value() == prompt.id().value():
                return Err(f'Prompt with id "{prompt.id().value()}" already exists.')
            if existing.name() == prompt.name():
                return Err(f'Prompt with name "{prompt.name()}" already exists.')
        return Ok(FavoritePrompts(self._prompts + (prompt,)))

    def update_prompt(self, prompt: FavoritePrompt) -> Result["FavoritePrompts", str]:
        new_prompts = []
        found = False
        for existing in self._prompts:
            if existing.id().value() == prompt.id().value():
                new_prompts.append(prompt)
                found = True
            else:
                new_prompts.append(existing)
        if not found:
            return Err(f'Prompt with id "{prompt.id().value()}" not found.')
        return Ok(FavoritePrompts(tuple(new_prompts)))

    def remove_prompt(
        self, prompt_id: FavoritePromptId
    ) -> Result["FavoritePrompts", str]:
        new_prompts = tuple(
            p for p in self._prompts if p.id().value() != prompt_id.value()
        )
        if len(new_prompts) == len(self._prompts):
            return Err(f'Prompt with id "{prompt_id.value()}" not found.')
        return Ok(FavoritePrompts(new_prompts))

    def find_prompt(
        self, prompt_id: FavoritePromptId
    ) -> Result[FavoritePrompt, str]:  # pragma: no cover - simple loop
        for prompt in self._prompts:
            if prompt.id().value() == prompt_id.value():
                return Ok(prompt)
        return Err(f'Prompt with id "{prompt_id.value()}" not found.')
