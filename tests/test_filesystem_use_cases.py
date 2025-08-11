from pathlib import Path

from codebase_to_llm.application.uc_create_file import CreateFileUseCase
from codebase_to_llm.application.uc_create_folder import CreateFolderUseCase
from codebase_to_llm.application.uc_delete_path import DeletePathUseCase
from codebase_to_llm.application.uc_rename_path import RenamePathUseCase
from codebase_to_llm.infrastructure.filesystem_file_manager import (
    FileSystemFileManager,
)


def test_create_file_use_case(tmp_path: Path) -> None:
    fs = FileSystemFileManager()
    use_case = CreateFileUseCase(fs)
    result = use_case.execute(tmp_path, "new.txt")
    assert result.is_ok()
    assert (tmp_path / "new.txt").exists()


def test_create_folder_use_case(tmp_path: Path) -> None:
    fs = FileSystemFileManager()
    use_case = CreateFolderUseCase(fs)
    result = use_case.execute(tmp_path, "folder")
    assert result.is_ok()
    assert (tmp_path / "folder").is_dir()


def test_rename_and_delete_use_cases(tmp_path: Path) -> None:
    fs = FileSystemFileManager()
    create_uc = CreateFileUseCase(fs)
    rename_uc = RenamePathUseCase(fs)
    delete_uc = DeletePathUseCase(fs)

    create_uc.execute(tmp_path, "file.txt")
    path = tmp_path / "file.txt"

    result = rename_uc.execute(path, "renamed.txt")
    assert result.is_ok()
    new_path = tmp_path / "renamed.txt"
    assert new_path.exists()

    result = delete_uc.execute(new_path)
    assert result.is_ok()
    assert not new_path.exists()
