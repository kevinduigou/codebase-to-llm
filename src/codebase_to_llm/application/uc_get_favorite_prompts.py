"""Use case for retrieving all favorite prompts."""

from __future__ import annotations

from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import FavoritePrompts
from codebase_to_llm.domain.result import Err, Ok, Result


class GetFavoritePromptsUseCase:
    """Loads favorite prompts from the repository."""

    def __init__(self, repo: FavoritePromptsRepositoryPort):
        self._repo = repo

    def execute(self) -> Result[FavoritePrompts, str]:
        load_result = self._repo.load_prompts()
        if load_result.is_err():
            empty_result = FavoritePrompts.try_create([])
            if empty_result.is_err():
                return Err(empty_result.err() or "Unknown error creating collection.")
            prompts = empty_result.ok()
            assert prompts is not None
            return Ok(prompts)
        prompts = load_result.ok()
        if prompts is None:
            empty_result = FavoritePrompts.try_create([])
            if empty_result.is_err():
                return Err(empty_result.err() or "Unknown error creating collection.")
            prompts = empty_result.ok()
        assert prompts is not None
        return Ok(prompts)
