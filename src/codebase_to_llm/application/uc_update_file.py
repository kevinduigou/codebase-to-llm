from __future__ import annotations

from codebase_to_llm.application.ports import FileRepositoryPort
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.domain.directory import DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class UpdateFileUseCase:
    """Use case for renaming or moving a file."""

    def __init__(self, file_repo: FileRepositoryPort) -> None:
        self._file_repo = file_repo

    def execute(
        self,
        owner_id_value: str,
        file_id_value: str,
        new_name: str | None = None,
        new_directory_id_value: str | None = None,
    ) -> Result[None, str]:
        owner_res = UserId.try_create(owner_id_value)
        if owner_res.is_err():
            return Err(owner_res.err() or "Invalid owner id")
        owner_id = owner_res.ok()
        assert owner_id is not None

        id_result = StoredFileId.try_create(file_id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid file id")
        file_id = id_result.ok()
        assert file_id is not None

        file_result = self._file_repo.get(file_id)
        if file_result.is_err():
            return Err(file_result.err() or "File not found")
        file = file_result.ok()
        assert file is not None

        if file.owner_id().value() != owner_id.value():
            return Err("Access denied")

        updated = file
        if new_name is not None:
            rename_result = file.rename(new_name)
            if rename_result.is_err():
                return Err(rename_result.err() or "Invalid file name")
            renamed = rename_result.ok()
            assert renamed is not None
            updated = renamed

        if new_directory_id_value is not None:
            dir_result = DirectoryId.try_create(new_directory_id_value)
            if dir_result.is_err():
                return Err(dir_result.err() or "Invalid directory id")
            new_dir = dir_result.ok()
            assert new_dir is not None
            updated = updated.move(new_dir)

        update_result = self._file_repo.update(updated)
        if update_result.is_err():
            return Err(update_result.err() or "Failed to update file")

        return Ok(None)
