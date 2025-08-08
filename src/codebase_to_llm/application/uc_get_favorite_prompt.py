"""Use case for retrieving a favorite prompt by id."""

from __future__ import annotations

from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import FavoritePrompt, FavoritePromptId
from codebase_to_llm.domain.result import Err, Ok, Result


class GetFavoritePromptUseCase:
    """Returns a favorite prompt matching the given id."""

    def __init__(self, repo: FavoritePromptsRepositoryPort):
        self._repo = repo

    def execute(self, id_value: str) -> Result[FavoritePrompt, str]:
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

        find_result = prompts.find_prompt(prompt_id)
        if find_result.is_err():
            return Err(find_result.err() or "Favorite prompt not found.")
        prompt = find_result.ok()
        assert prompt is not None
        return Ok(prompt)
