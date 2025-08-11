from __future__ import annotations

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import ApiKey, ApiKeyAddedEvent
from codebase_to_llm.domain.result import Result, Ok, Err


class AddApiKeyUseCase:
    """Use case for adding a new API key."""

    def __init__(self, api_key_repo: ApiKeyRepositoryPort):
        self._api_key_repo = api_key_repo

    def execute(
        self,
        user_id_value: str,
        id_value: str,
        url_provider: str,
        api_key_value: str,
    ) -> Result[ApiKeyAddedEvent, str]:
        """
        Executes the add API key use case.

        Args:
            user_id_value: Identifier of the owner
            id_value: Unique identifier for the API key
            url_provider: URL of the API provider
            api_key_value: The actual API key value

        Returns:
            Result containing ApiKeyAddedEvent or error message
        """
        # Create the API key domain object
        api_key_result = ApiKey.try_create(
            id_value, user_id_value, url_provider, api_key_value
        )
        if api_key_result.is_err():
            return Err(api_key_result.err() or "Failed to create API key object.")

        api_key = api_key_result.ok()
        if api_key is None:
            return Err("Failed to create API key object.")

        # Load existing API keys
        existing_keys_result = self._api_key_repo.load_api_keys()
        if existing_keys_result.is_err():
            return Err(
                f"Failed to load existing API keys: {existing_keys_result.err() or 'Unknown error.'}"
            )

        existing_keys = existing_keys_result.ok()
        if existing_keys is None:
            return Err("Failed to load existing API keys.")

        # Add the new API key
        updated_keys_result = existing_keys.add_api_key(api_key)
        if updated_keys_result.is_err():
            return Err(
                updated_keys_result.err() or "Failed to add API key to collection."
            )

        updated_keys = updated_keys_result.ok()
        if updated_keys is None:
            return Err("Failed to add API key to collection.")

        # Save the updated collection
        save_result = self._api_key_repo.save_api_keys(updated_keys)
        if save_result.is_err():
            return Err(
                f"Failed to save API keys: {save_result.err() or 'Unknown error.'}"
            )

        return Ok(ApiKeyAddedEvent(api_key))
