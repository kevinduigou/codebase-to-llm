from pathlib import Path

from codebase_to_llm.application.ports import (
    DirectoryRepositoryPort,
    PromptRepositoryPort,
)
from codebase_to_llm.domain.prompt import (
    FileAddedAsPromptVariableEvent,
    set_prompt_variable,
)
from codebase_to_llm.domain.result import Err, Ok, Result


class AddFileAsPromptVariableUseCase:
    """Use case for adding a file as a prompt variable."""

    def __init__(self, prompt_repository: PromptRepositoryPort) -> None:
        self.prompt_repository = prompt_repository

    def execute(
        self,
        file_repository: DirectoryRepositoryPort,
        variable_key: str,
        relative_path: Path,
    ) -> Result[FileAddedAsPromptVariableEvent, str]:
        """
        Add a file as a prompt variable.

        Args:
            file_path: The relative path to the file to add as a prompt variable.
            variable_key: The key to use for the prompt variable.

        Returns:
            A result containing a FileAddedAsPromptVariableEvent or an error string.
        """
        file_content_result = file_repository.read_file(relative_path)
        if file_content_result.is_err():
            return Err(file_content_result.err() or "Could not read file content")

        file_content = file_content_result.ok()
        if file_content is None:
            return Err(f"File is empty: {relative_path}")

        prompt_result = self.prompt_repository.get_prompt()
        if prompt_result.is_err():
            return Err(prompt_result.err() or "Could not get prompt")

        prompt = prompt_result.ok()

        if prompt is None:
            return Err("No prompt set")

        new_prompt = set_prompt_variable(prompt, variable_key, file_content)
        prompt_variable_result = self.prompt_repository.set_prompt(new_prompt)
        if prompt_variable_result.is_err():
            return Err(prompt_variable_result.err() or "Could not set prompt variable")
        return Ok(
            FileAddedAsPromptVariableEvent(
                str(relative_path), variable_key, file_content
            )
        )
