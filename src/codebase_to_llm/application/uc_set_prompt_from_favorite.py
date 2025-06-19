from __future__ import annotations

from dataclasses import dataclass
from codebase_to_llm.application.ports import PromptRepositoryPort
from codebase_to_llm.domain.prompt import Prompt
from codebase_to_llm.domain.result import Result, Err, Ok


@dataclass
class AddPromptFromFavoriteLisUseCase:
    """Set the user prompt from a favorite prompt and save it via repository."""

    _prompt_repo: PromptRepositoryPort

    def execute(self, content: str) -> Result[Prompt, str]:
        prompt_result = Prompt.try_create(content)
        if prompt_result.is_err():
            return Err(prompt_result.err() or "Unknown error")
        prompt = prompt_result.ok()
        if prompt is None:
            return Err("Prompt creation failed")
        save_result = self._prompt_repo.set_prompt(prompt)
        if save_result.is_err():
            return Err(save_result.err() or "Unknown error")
        return Ok(prompt)
