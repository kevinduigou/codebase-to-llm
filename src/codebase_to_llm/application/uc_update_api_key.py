from __future__ import annotations

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import (
    ApiKeyId,
    UrlProvider,
    ApiKeyValue,
    ApiKeyUpdatedEvent,
)
from codebase_to_llm.domain.result import Result, Ok, Err


class UpdateApiKeyUseCase:
    """Use case for updating an existing API key."""

    def __init__(self, api_key_repo: ApiKeyRepositoryPort):
        self._api_key_repo = api_key_repo

    def execute(
        self, api_key_id: str, new_url_provider: str, new_api_key_value: str
    ) -> Result[ApiKeyUpdatedEvent, str]:
        """
        Executes the update API key use case.

        Args:
            api_key_id: ID of the API key to update
            new_url_provider: New URL provider
            new_api_key_value: New API key value

        Returns:
            Result containing ApiKeyUpdatedEvent or error message
        """
        # Validate inputs
        id_result = ApiKeyId.try_create(api_key_id)
        if id_result.is_err():
            return Err(f"Invalid API Key ID: {id_result.err()}")

        url_result = UrlProvider.try_create(new_url_provider)
        if url_result.is_err():
            return Err(f"Invalid URL Provider: {url_result.err()}")

        key_value_result = ApiKeyValue.try_create(new_api_key_value)
        if key_value_result.is_err():
            return Err(f"Invalid API Key Value: {key_value_result.err()}")

        api_key_id_obj = id_result.ok()
        new_url = url_result.ok()
        new_key_value = key_value_result.ok()

        # Load existing API keys
        existing_keys_result = self._api_key_repo.load_api_keys()
        if existing_keys_result.is_err():
            return Err(
                f"Failed to load existing API keys: {existing_keys_result.err()}"
            )

        existing_keys = existing_keys_result.ok()

        # Find the API key to update
        api_key_result = existing_keys.find_by_id(api_key_id_obj)
        if api_key_result.is_err():
            return Err(api_key_result.err())

        api_key = api_key_result.ok()

        # Update the API key
        updated_api_key = api_key.update_url_provider(new_url).update_api_key_value(
            new_key_value
        )

        # Update the collection
        updated_keys_result = existing_keys.update_api_key(updated_api_key)
        if updated_keys_result.is_err():
            return Err(updated_keys_result.err())

        updated_keys = updated_keys_result.ok()

        # Save the updated collection
        save_result = self._api_key_repo.save_api_keys(updated_keys)
        if save_result.is_err():
            return Err(f"Failed to save API keys: {save_result.err()}")

        return Ok(ApiKeyUpdatedEvent(updated_api_key))
