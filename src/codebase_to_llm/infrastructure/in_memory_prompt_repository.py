from __future__ import annotations

from typing_extensions import final

from codebase_to_llm.application.ports import PromptRepositoryPort
from codebase_to_llm.domain.prompt import Prompt
from codebase_to_llm.domain.result import Result, Ok


@final
class InMemoryPromptRepository(PromptRepositoryPort):
    """Simple in-memory storage for the user prompt."""

    __slots__ = ("_prompt",)

    def __init__(self) -> None:
        self._prompt: Prompt | None = None

    def set_prompt(self, prompt: Prompt) -> Result[None, str]:
        self._prompt = prompt
        return Ok(None)

    def get_prompt(self) -> Result[Prompt | None, str]:
        return Ok(self._prompt)
