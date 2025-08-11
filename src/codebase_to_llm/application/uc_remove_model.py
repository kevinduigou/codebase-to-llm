from __future__ import annotations

from codebase_to_llm.application.ports import ModelRepositoryPort
from codebase_to_llm.domain.model import ModelId, ModelRemovedEvent
from codebase_to_llm.domain.result import Result, Ok, Err


class RemoveModelUseCase:
    """Use case for removing a model."""

    def __init__(self, model_repo: ModelRepositoryPort) -> None:
        self._model_repo = model_repo

    def execute(self, model_id_value: str) -> Result[ModelRemovedEvent, str]:
        model_id_result = ModelId.try_create(model_id_value)
        if model_id_result.is_err():
            return Err(model_id_result.err() or "Invalid model ID.")

        model_id = model_id_result.ok()
        if model_id is None:
            return Err("Invalid model ID.")

        models_result = self._model_repo.load_models()
        if models_result.is_err():
            return Err(models_result.err() or "Failed to load models.")

        models = models_result.ok()
        if models is None:
            return Err("Failed to load models.")

        updated_models_result = models.remove_model(model_id)
        if updated_models_result.is_err():
            return Err(updated_models_result.err() or "Failed to remove model.")

        updated_models = updated_models_result.ok()
        if updated_models is None:
            return Err("Failed to remove model.")

        save_result = self._model_repo.save_models(updated_models)
        if save_result.is_err():
            return Err(
                f"Failed to save models: {save_result.err() or 'Unknown error.'}"
            )

        return Ok(ModelRemovedEvent(model_id))
