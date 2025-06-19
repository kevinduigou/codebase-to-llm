from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.application.ports import PromptRepositoryPort
from codebase_to_llm.domain.prompt import Prompt
from codebase_to_llm.domain.result import Err, Ok, Result


@dataclass
class AddPromptFromFileUseCase:
    """Load a file as the user prompt and save it via repository."""

    _prompt_repo: PromptRepositoryPort

    def execute(self, path: Path) -> Result[Prompt, str]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

        prompt_result = Prompt.try_create(text)
        if prompt_result.is_err():
            return Err(prompt_result.err() or "Unknown error")
        prompt = prompt_result.ok()
        if prompt is None:
            return Err("Prompt creation failed")

        save_result = self._prompt_repo.set_prompt(prompt)
        if save_result.is_err():
            return Err(save_result.err() or "Unknown error")
        return Ok(prompt)
