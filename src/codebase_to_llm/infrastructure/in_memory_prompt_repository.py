from __future__ import annotations

from typing_extensions import final

from codebase_to_llm.application.ports import PromptRepositoryPort
from codebase_to_llm.domain.prompt import (
    Prompt,
    PromptVariable,
    set_prompt_variable as domain_set_prompt_variable,
)
from codebase_to_llm.domain.result import Result, Ok, Err


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
        if self._prompt is None:
            return Ok(None)
        return Ok(self._prompt)

    def set_prompt_variable(self, variable_key: str, content: str) -> Result[None, str]:
        if self._prompt is None:
            return Err("No prompt set to add variables to")
        self._prompt = domain_set_prompt_variable(self._prompt, variable_key, content)
        return Ok(None)

    def get_variables_in_prompt(self) -> Result[list[PromptVariable], str]:
        if self._prompt is None:
            return Ok([])
        return Ok(self._prompt.get_variables())
