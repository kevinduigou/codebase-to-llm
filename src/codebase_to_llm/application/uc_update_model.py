from __future__ import annotations

from codebase_to_llm.application.ports import ModelRepositoryPort, ApiKeyRepositoryPort
from codebase_to_llm.domain.model import Model, ModelUpdatedEvent
from codebase_to_llm.domain.result import Result, Ok, Err


class UpdateModelUseCase:
    """Use case for updating a model."""

    def __init__(
        self, model_repo: ModelRepositoryPort, api_key_repo: ApiKeyRepositoryPort
    ) -> None:
        self._model_repo = model_repo
        self._api_key_repo = api_key_repo

    def execute(
        self,
        user_id_value: str,
        model_id: str,
        new_name: str,
        new_api_key_id: str,
    ) -> Result[ModelUpdatedEvent, str]:
        model_result = Model.try_create(
            model_id, user_id_value, new_name, new_api_key_id
        )
        if model_result.is_err():
            return Err(model_result.err() or "Failed to create model object.")

        model = model_result.ok()
        if model is None:
            return Err("Failed to create model object.")

        api_key_result = self._api_key_repo.find_api_key_by_id(model.api_key_id())
        if api_key_result.is_err():
            return Err(api_key_result.err() or "API key not found.")

        models_result = self._model_repo.load_models()
        if models_result.is_err():
            return Err(models_result.err() or "Failed to load models.")

        models = models_result.ok()
        if models is None:
            return Err("Failed to load models.")

        updated_models_result = models.update_model(model)
        if updated_models_result.is_err():
            return Err(updated_models_result.err() or "Failed to update model.")

        updated_models = updated_models_result.ok()
        if updated_models is None:
            return Err("Failed to update model.")

        save_result = self._model_repo.save_models(updated_models)
        if save_result.is_err():
            return Err(
                f"Failed to save models: {save_result.err() or 'Unknown error.'}"
            )

        return Ok(ModelUpdatedEvent(model))
