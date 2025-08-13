from __future__ import annotations

from codebase_to_llm.application.ports import FileRepositoryPort, FileStoragePort
from codebase_to_llm.domain.stored_file import StoredFileId, StoredFile
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class GetFileUseCase:
    """Use case for retrieving a file and its content."""

    def __init__(self, file_repo: FileRepositoryPort, storage: FileStoragePort) -> None:
        self._file_repo = file_repo
        self._storage = storage

    def execute(
        self, owner_id_value: str, file_id_value: str
    ) -> Result[tuple[StoredFile, bytes], str]:
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

        content_result = self._storage.load(file)
        if content_result.is_err():
            return Err(content_result.err() or "Failed to load file content")
        content = content_result.ok()
        assert content is not None

        return Ok((file, content))
