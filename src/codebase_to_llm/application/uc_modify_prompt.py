"""Use case for modifying the prompt."""

from __future__ import annotations

from codebase_to_llm.application.ports import PromptRepositoryPort
from codebase_to_llm.domain.prompt import Prompt, PromptHasBeenModifiedEvent
from codebase_to_llm.domain.result import Err, Ok, Result


class ModifyPromptUseCase:
    """Modifies the prompt content."""

    def __init__(self, prompt_repo: PromptRepositoryPort):
        self._prompt_repo = prompt_repo

    def execute(self, new_content: str) -> Result[PromptHasBeenModifiedEvent, str]:
        """
        Executes the use case.

        Args:
            new_content: The new content for the prompt.

        Returns:
            A result containing the modified prompt or an error.
        """
        variables_from_repo_result = self._prompt_repo.get_variables_in_prompt()
        if variables_from_repo_result.is_err():
            error = variables_from_repo_result.err()
            return Err(
                error if error is not None else "Unknown error getting variables"
            )
        variables = variables_from_repo_result.ok()
        # Reinjecting variables from previous prompt
        if variables is None:
            variables = []
        new_prompt_result = Prompt.try_create(new_content, variables)

        if new_prompt_result.is_err():
            error = new_prompt_result.err()
            return Err(error if error is not None else "Unknown error creating prompt")

        new_prompt = new_prompt_result.ok()
        if new_prompt is None:
            new_prompt = Prompt("", [])

        self._prompt_repo.set_prompt(new_prompt)

        return Ok(PromptHasBeenModifiedEvent(new_prompt))
