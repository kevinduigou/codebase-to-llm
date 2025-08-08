"""Use case for removing a favorite prompt."""

from __future__ import annotations

from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import FavoritePromptId
from codebase_to_llm.domain.result import Err, Ok, Result


class RemoveFavoritePromptUseCase:
    """Removes a favorite prompt identified by its id."""

    def __init__(self, repo: FavoritePromptsRepositoryPort):
        self._repo = repo

    def execute(self, id_value: str) -> Result[None, str]:
        id_result = FavoritePromptId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid id")
        prompt_id = id_result.ok()
        assert prompt_id is not None

        load_result = self._repo.load_prompts()
        if load_result.is_err():
            return Err(load_result.err() or "Failed to load favorite prompts.")
        prompts = load_result.ok()
        if prompts is None:
            return Err("Failed to load favorite prompts.")

        remove_result = prompts.remove_prompt(prompt_id)
        if remove_result.is_err():
            return Err(remove_result.err() or "Failed to remove favorite prompt.")
        updated_prompts = remove_result.ok()
        assert updated_prompts is not None

        save_result = self._repo.save_prompts(updated_prompts)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save favorite prompts.")

        return Ok(None)
