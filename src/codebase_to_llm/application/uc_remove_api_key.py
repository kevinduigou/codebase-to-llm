from __future__ import annotations

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import ApiKeyId, ApiKeyRemovedEvent
from codebase_to_llm.domain.result import Result, Ok, Err


class RemoveApiKeyUseCase:
    """Use case for removing an API key."""

    def __init__(self, api_key_repo: ApiKeyRepositoryPort):
        self._api_key_repo = api_key_repo

    def execute(self, api_key_id: str) -> Result[ApiKeyRemovedEvent, str]:
        """
        Executes the remove API key use case.

        Args:
            api_key_id: ID of the API key to remove

        Returns:
            Result containing ApiKeyRemovedEvent or error message
        """
        # Validate input
        id_result = ApiKeyId.try_create(api_key_id)
        if id_result.is_err():
            return Err(f"Invalid API Key ID: {id_result.err() or 'Unknown error.'}")

        api_key_id_obj = id_result.ok()
        if api_key_id_obj is None:
            return Err("Failed to create ApiKeyId object.")

        # Load existing API keys
        existing_keys_result = self._api_key_repo.load_api_keys()
        if existing_keys_result.is_err():
            return Err(
                f"Failed to load existing API keys: {existing_keys_result.err() or 'Unknown error.'}"
            )

        existing_keys = existing_keys_result.ok()
        if existing_keys is None:
            return Err("Failed to load existing API keys.")

        # Remove the API key
        updated_keys_result = existing_keys.remove_api_key(api_key_id_obj)
        if updated_keys_result.is_err():
            return Err(
                updated_keys_result.err() or "Failed to remove API key from collection."
            )

        updated_keys = updated_keys_result.ok()
        if updated_keys is None:
            return Err("Failed to remove API key from collection.")

        # Save the updated collection
        save_result = self._api_key_repo.save_api_keys(updated_keys)
        if save_result.is_err():
            return Err(
                f"Failed to save API keys: {save_result.err() or 'Unknown error.'}"
            )

        return Ok(ApiKeyRemovedEvent(api_key_id_obj))
