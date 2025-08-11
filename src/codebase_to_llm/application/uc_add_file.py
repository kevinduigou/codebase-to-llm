from __future__ import annotations

from codebase_to_llm.application.ports import FileRepositoryPort, FileStoragePort
from codebase_to_llm.domain.stored_file import StoredFile
from codebase_to_llm.domain.directory import DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class AddFileUseCase:
    """Use case for creating and persisting a file."""

    def __init__(self, file_repo: FileRepositoryPort, storage: FileStoragePort) -> None:
        self._file_repo = file_repo
        self._storage = storage

    def execute(
        self,
        id_value: str,
        owner_id_value: str,
        name: str,
        content: bytes,
        directory_id_value: str | None = None,
    ) -> Result[StoredFile, str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner id")
        owner_id = owner_result.ok()
        assert owner_id is not None

        directory_id = None
        if directory_id_value is not None:
            dir_result = DirectoryId.try_create(directory_id_value)
            if dir_result.is_err():
                return Err(dir_result.err() or "Invalid directory id")
            directory_id = dir_result.ok()
            assert directory_id is not None

        file_result = StoredFile.try_create(id_value, owner_id, name, directory_id)
        if file_result.is_err():
            return Err(file_result.err() or "Invalid file data")
        file = file_result.ok()
        assert file is not None

        repo_result = self._file_repo.add(file)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to save file metadata")

        storage_result = self._storage.save(file, content)
        if storage_result.is_err():
            return Err(storage_result.err() or "Failed to store file")

        return Ok(file)
