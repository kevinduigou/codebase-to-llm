from __future__ import annotations

from codebase_to_llm.application.ports import ModelRepositoryPort, ApiKeyRepositoryPort
from codebase_to_llm.domain.model import Model, ModelAddedEvent
from codebase_to_llm.domain.result import Result, Ok, Err


class AddModelUseCase:
    """Use case for adding a new model."""

    def __init__(
        self, model_repo: ModelRepositoryPort, api_key_repo: ApiKeyRepositoryPort
    ) -> None:
        self._model_repo = model_repo
        self._api_key_repo = api_key_repo

    def execute(
        self,
        user_id_value: str,
        id_value: str,
        name: str,
        api_key_id_value: str,
    ) -> Result[ModelAddedEvent, str]:
        model_result = Model.try_create(id_value, user_id_value, name, api_key_id_value)
        if model_result.is_err():
            return Err(model_result.err() or "Failed to create model object.")

        model = model_result.ok()
        if model is None:
            return Err("Failed to create model object.")

        api_key_result = self._api_key_repo.find_api_key_by_id(model.api_key_id())
        if api_key_result.is_err():
            return Err(api_key_result.err() or "API key not found.")

        existing_models_result = self._model_repo.load_models()
        if existing_models_result.is_err():
            return Err(
                f"Failed to load existing models: {existing_models_result.err() or 'Unknown error.'}"
            )

        existing_models = existing_models_result.ok()
        if existing_models is None:
            return Err("Failed to load existing models.")

        updated_models_result = existing_models.add_model(model)
        if updated_models_result.is_err():
            return Err(
                updated_models_result.err() or "Failed to add model to collection."
            )

        updated_models = updated_models_result.ok()
        if updated_models is None:
            return Err("Failed to add model to collection.")

        save_result = self._model_repo.save_models(updated_models)
        if save_result.is_err():
            return Err(
                f"Failed to save models: {save_result.err() or 'Unknown error.'}"
            )

        return Ok(ModelAddedEvent(model))
