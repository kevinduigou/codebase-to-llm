from __future__ import annotations

from codebase_to_llm.application.ports import DirectoryStructureRepositoryPort
from codebase_to_llm.domain.directory import DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class UpdateDirectoryUseCase:
    """Use case for renaming or moving a directory."""

    def __init__(self, repo: DirectoryStructureRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        owner_id_value: str,
        id_value: str,
        new_name: str | None = None,
        new_parent_id_value: str | None = None,
    ) -> Result[None, str]:
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

        dir_result = self._repo.get(dir_id)
        if dir_result.is_err():
            return Err(dir_result.err() or "Directory not found")
        directory = dir_result.ok()
        assert directory is not None
        if directory.owner_id().value() != owner_id.value():
            return Err("Access denied")

        updated = directory
        if new_name is not None:
            rename_result = directory.rename(new_name)
            if rename_result.is_err():
                return Err(rename_result.err() or "Invalid directory name")
            renamed = rename_result.ok()
            assert renamed is not None
            updated = renamed

        if new_parent_id_value is not None:
            parent_result = DirectoryId.try_create(new_parent_id_value)
            if parent_result.is_err():
                return Err(parent_result.err() or "Invalid parent id")
            parent_id = parent_result.ok()
            assert parent_id is not None
            updated = updated.move(parent_id)

        update_result = self._repo.update(updated)
        if update_result.is_err():
            return Err(update_result.err() or "Failed to update directory")

        return Ok(None)
