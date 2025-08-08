"""Use case for adding a favorite prompt."""

from __future__ import annotations

import uuid

from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import (
    FavoritePrompt,
    FavoritePrompts,
)
from codebase_to_llm.domain.result import Err, Ok, Result


class AddFavoritePromptUseCase:
    """Adds a new favorite prompt and persists it."""

    def __init__(self, repo: FavoritePromptsRepositoryPort):
        self._repo = repo

    def execute(self, name: str, content: str) -> Result[FavoritePrompt, str]:
        new_id = str(uuid.uuid4())
        prompt_result = FavoritePrompt.try_create(new_id, name, content)
        if prompt_result.is_err():
            return Err(prompt_result.err() or "Failed to create favorite prompt.")
        prompt = prompt_result.ok()
        if prompt is None:
            return Err("Failed to create favorite prompt.")

        load_result = self._repo.load_prompts()
        if load_result.is_err():
            empty_result = FavoritePrompts.try_create([])
            if empty_result.is_err():
                return Err(empty_result.err() or "Unknown error creating collection.")
            prompts = empty_result.ok()
        else:
            prompts = load_result.ok()

        if prompts is None:
            empty_result = FavoritePrompts.try_create([])
            if empty_result.is_err():
                return Err(empty_result.err() or "Unknown error creating collection.")
            prompts = empty_result.ok()

        assert prompts is not None
        add_result = prompts.add_prompt(prompt)
        if add_result.is_err():
            return Err(add_result.err() or "Failed to add favorite prompt.")
        updated_prompts = add_result.ok()
        assert updated_prompts is not None

        save_result = self._repo.save_prompts(updated_prompts)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save favorite prompts.")

        return Ok(prompt)
