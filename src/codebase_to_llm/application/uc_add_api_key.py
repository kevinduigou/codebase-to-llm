from __future__ import annotations

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import ApiKey, ApiKeyAddedEvent
from codebase_to_llm.domain.result import Result, Ok, Err


class AddApiKeyUseCase:
    """Use case for adding a new API key."""

    def __init__(self, api_key_repo: ApiKeyRepositoryPort):
        self._api_key_repo = api_key_repo

    def execute(
        self, id_value: str, url_provider: str, api_key_value: str
    ) -> Result[ApiKeyAddedEvent, str]:
        """
        Executes the add API key use case.

        Args:
            id_value: Unique identifier for the API key
            url_provider: URL of the API provider
            api_key_value: The actual API key value

        Returns:
            Result containing ApiKeyAddedEvent or error message
        """
        # Create the API key domain object
        api_key_result = ApiKey.try_create(id_value, url_provider, api_key_value)
        if api_key_result.is_err():
            return Err(api_key_result.err())

        api_key = api_key_result.ok()

        # Load existing API keys
        existing_keys_result = self._api_key_repo.load_api_keys()
        if existing_keys_result.is_err():
            return Err(
                f"Failed to load existing API keys: {existing_keys_result.err()}"
            )

        existing_keys = existing_keys_result.ok()

        # Add the new API key
        updated_keys_result = existing_keys.add_api_key(api_key)
        if updated_keys_result.is_err():
            return Err(updated_keys_result.err())

        updated_keys = updated_keys_result.ok()

        # Save the updated collection
        save_result = self._api_key_repo.save_api_keys(updated_keys)
        if save_result.is_err():
            return Err(f"Failed to save API keys: {save_result.err()}")

        return Ok(ApiKeyAddedEvent(api_key))
