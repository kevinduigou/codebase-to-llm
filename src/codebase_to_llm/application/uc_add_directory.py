from __future__ import annotations

from codebase_to_llm.application.ports import DirectoryStructureRepositoryPort
from codebase_to_llm.domain.directory import Directory, DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class AddDirectoryUseCase:
    """Use case for creating a directory."""

    def __init__(self, repo: DirectoryStructureRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        id_value: str,
        owner_id_value: str,
        name: str,
        parent_id_value: str | None = None,
    ) -> Result[Directory, str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner id")
        owner_id = owner_result.ok()
        assert owner_id is not None

        parent_id = None
        if parent_id_value is not None:
            parent_result = DirectoryId.try_create(parent_id_value)
            if parent_result.is_err():
                return Err(parent_result.err() or "Invalid parent id")
            parent_id = parent_result.ok()
            assert parent_id is not None

        dir_result = Directory.try_create(id_value, owner_id, name, parent_id)
        if dir_result.is_err():
            return Err(dir_result.err() or "Invalid directory data")
        directory = dir_result.ok()
        assert directory is not None

        save_result = self._repo.add(directory)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save directory")

        return Ok(directory)
