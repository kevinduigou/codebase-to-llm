from __future__ import annotations

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import ApiKeys
from codebase_to_llm.domain.result import Result


class LoadApiKeysUseCase:
    """Use case for loading all API keys."""

    def __init__(self, api_key_repo: ApiKeyRepositoryPort):
        self._api_key_repo = api_key_repo

    def execute(self) -> Result[ApiKeys, str]:
        """
        Executes the load API keys use case.

        Returns:
            Result containing ApiKeys collection or error message
        """
        return self._api_key_repo.load_api_keys()
