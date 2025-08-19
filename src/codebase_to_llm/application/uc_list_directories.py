from __future__ import annotations

from codebase_to_llm.application.ports import DirectoryStructureRepositoryPort
from codebase_to_llm.domain.directory import Directory
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class ListDirectoriesUseCase:
    """Use case for listing all directories owned by a user."""

    def __init__(self, repo: DirectoryStructureRepositoryPort) -> None:
        self._repo = repo

    def execute(self, owner_id_value: str) -> Result[list[Directory], str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner id")
        owner_id = owner_result.ok()
        assert owner_id is not None

        repo_result = self._repo.list_for_user(owner_id)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to list directories")
        directories = repo_result.ok()
        assert directories is not None
        return Ok(directories)
