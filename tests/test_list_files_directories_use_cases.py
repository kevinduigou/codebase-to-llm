from codebase_to_llm.application.ports import (
    FileRepositoryPort,
    DirectoryStructureRepositoryPort,
)
from codebase_to_llm.application.uc_list_files import ListFilesUseCase
from codebase_to_llm.application.uc_list_directories import ListDirectoriesUseCase
from codebase_to_llm.domain.stored_file import StoredFile, StoredFileId
from codebase_to_llm.domain.directory import Directory, DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class StubFileRepo(FileRepositoryPort):
    def __init__(self, files: list[StoredFile]) -> None:
        self._files = files

    def add(self, file: StoredFile) -> Result[None, str]:  # type: ignore[override]
        return Ok(None)

    def get(self, file_id: StoredFileId) -> Result[StoredFile, str]:  # type: ignore[override]
        return Err("not implemented")

    def update(self, file: StoredFile) -> Result[None, str]:  # type: ignore[override]
        return Ok(None)

    def remove(self, file_id: StoredFileId) -> Result[None, str]:  # type: ignore[override]
        return Ok(None)

    def list_for_user(self, owner_id: UserId) -> Result[list[StoredFile], str]:  # type: ignore[override]
        return Ok([f for f in self._files if f.owner_id().value() == owner_id.value()])


class StubDirectoryRepo(DirectoryStructureRepositoryPort):
    def __init__(self, directories: list[Directory]) -> None:
        self._dirs = directories

    def add(self, directory: Directory) -> Result[None, str]:  # type: ignore[override]
        return Ok(None)

    def get(self, directory_id: DirectoryId) -> Result[Directory, str]:  # type: ignore[override]
        return Err("not implemented")

    def update(self, directory: Directory) -> Result[None, str]:  # type: ignore[override]
        return Ok(None)

    def remove(self, directory_id: DirectoryId) -> Result[None, str]:  # type: ignore[override]
        return Ok(None)

    def list_for_user(self, owner_id: UserId) -> Result[list[Directory], str]:  # type: ignore[override]
        return Ok([d for d in self._dirs if d.owner_id().value() == owner_id.value()])


def test_list_files_use_case_filters_by_owner() -> None:
    owner_res = UserId.try_create("u1")
    assert owner_res.is_ok()
    owner = owner_res.ok()
    assert owner is not None
    other_res = UserId.try_create("u2")
    assert other_res.is_ok()
    other = other_res.ok()
    assert other is not None
    f1_res = StoredFile.try_create("f1", owner, "file1.txt")
    f2_res = StoredFile.try_create("f2", other, "file2.txt")
    assert f1_res.is_ok() and f2_res.is_ok()
    repo = StubFileRepo([f1_res.ok(), f2_res.ok()])
    use_case = ListFilesUseCase(repo)
    result = use_case.execute(owner.value())
    assert result.is_ok()
    files = result.ok()
    assert files == [f1_res.ok()]


def test_list_directories_use_case_filters_by_owner() -> None:
    owner_res = UserId.try_create("u1")
    assert owner_res.is_ok()
    owner = owner_res.ok()
    assert owner is not None
    other_res = UserId.try_create("u2")
    assert other_res.is_ok()
    other = other_res.ok()
    assert other is not None
    d1_res = Directory.try_create("d1", owner, "dir1")
    d2_res = Directory.try_create("d2", other, "dir2")
    assert d1_res.is_ok() and d2_res.is_ok()
    repo = StubDirectoryRepo([d1_res.ok(), d2_res.ok()])
    use_case = ListDirectoriesUseCase(repo)
    result = use_case.execute(owner.value())
    assert result.is_ok()
    dirs = result.ok()
    assert dirs == [d1_res.ok()]
