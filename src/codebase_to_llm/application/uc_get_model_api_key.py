from __future__ import annotations

from typing import Tuple, final

from codebase_to_llm.application.ports import ApiKeyRepositoryPort, ModelRepositoryPort
from codebase_to_llm.domain.api_key import ApiKey
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.result import Err, Ok, Result


@final
class GetModelApiKeyUseCase:
    """Retrieve the model name and its associated API key."""

    def execute(
        self,
        model_id: ModelId,
        model_repo: ModelRepositoryPort,
        api_key_repo: ApiKeyRepositoryPort,
    ) -> Result[Tuple[str, ApiKey], str]:
        model_result = model_repo.find_model_by_id(model_id)
        if model_result.is_err():
            return Err(model_result.err() or "Error retrieving model")

        model = model_result.ok()
        if model is None:
            return Err("Model not found")

        api_key_result = api_key_repo.find_api_key_by_id(model.api_key_id())
        if api_key_result.is_err():
            return Err(api_key_result.err() or "Error retrieving API key")

        api_key = api_key_result.ok()
        if api_key is None:
            return Err("API key not found")

        return Ok((model.name().value(), api_key))
