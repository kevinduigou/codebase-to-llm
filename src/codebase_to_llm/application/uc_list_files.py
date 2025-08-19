from __future__ import annotations

from codebase_to_llm.application.ports import FileRepositoryPort
from codebase_to_llm.domain.stored_file import StoredFile
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class ListFilesUseCase:
    """Use case for listing all files owned by a user."""

    def __init__(self, file_repo: FileRepositoryPort) -> None:
        self._file_repo = file_repo

    def execute(self, owner_id_value: str) -> Result[list[StoredFile], str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner id")
        owner_id = owner_result.ok()
        assert owner_id is not None

        repo_result = self._file_repo.list_for_user(owner_id)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to list files")
        files = repo_result.ok()
        assert files is not None
        return Ok(files)
