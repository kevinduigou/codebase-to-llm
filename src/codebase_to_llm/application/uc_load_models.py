from __future__ import annotations

from codebase_to_llm.application.ports import ModelRepositoryPort
from codebase_to_llm.domain.model import Models
from codebase_to_llm.domain.result import Result


class LoadModelsUseCase:
    """Use case for loading all models."""

    def __init__(self, model_repo: ModelRepositoryPort) -> None:
        self._model_repo = model_repo

    def execute(self) -> Result[Models, str]:
        return self._model_repo.load_models()
