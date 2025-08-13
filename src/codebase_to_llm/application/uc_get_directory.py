from __future__ import annotations

from codebase_to_llm.application.ports import DirectoryStructureRepositoryPort
from codebase_to_llm.domain.directory import DirectoryId, Directory
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class GetDirectoryUseCase:
    """Use case for retrieving a directory."""

    def __init__(self, repo: DirectoryStructureRepositoryPort) -> None:
        self._repo = repo

    def execute(self, owner_id_value: str, id_value: str) -> Result[Directory, str]:
        owner_res = UserId.try_create(owner_id_value)
        if owner_res.is_err():
            return Err(owner_res.err() or "Invalid owner id")
        owner_id = owner_res.ok()
        assert owner_id is not None

        dir_id_result = DirectoryId.try_create(id_value)
        if dir_id_result.is_err():
            return Err(dir_id_result.err() or "Invalid directory id")
        dir_id = dir_id_result.ok()
        assert dir_id is not None

        result = self._repo.get(dir_id)
        if result.is_err():
            return Err(result.err() or "Directory not found")
        directory = result.ok()
        assert directory is not None
        if directory.owner_id().value() != owner_id.value():
            return Err("Access denied")
        return Ok(directory)
