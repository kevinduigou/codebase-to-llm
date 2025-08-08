"""Use case for updating an existing favorite prompt."""

from __future__ import annotations

from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import FavoritePrompt
from codebase_to_llm.domain.result import Err, Ok, Result


class UpdateFavoritePromptUseCase:
    """Updates a favorite prompt identified by its id."""

    def __init__(self, repo: FavoritePromptsRepositoryPort):
        self._repo = repo

    def execute(
        self, id_value: str, name: str, content: str
    ) -> Result[FavoritePrompt, str]:
        prompt_result = FavoritePrompt.try_create(id_value, name, content)
        if prompt_result.is_err():
            return Err(prompt_result.err() or "Failed to create favorite prompt.")
        prompt = prompt_result.ok()
        if prompt is None:
            return Err("Failed to create favorite prompt.")

        load_result = self._repo.load_prompts()
        if load_result.is_err():
            return Err(load_result.err() or "Failed to load favorite prompts.")
        prompts = load_result.ok()
        if prompts is None:
            return Err("Failed to load favorite prompts.")

        update_result = prompts.update_prompt(prompt)
        if update_result.is_err():
            return Err(update_result.err() or "Failed to update favorite prompt.")
        updated_prompts = update_result.ok()
        assert updated_prompts is not None

        save_result = self._repo.save_prompts(updated_prompts)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save favorite prompts.")

        return Ok(prompt)
