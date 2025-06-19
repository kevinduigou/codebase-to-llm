from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)


def test_create_and_delete(tmp_path: Path):
    repo = FileSystemDirectoryRepository(tmp_path)
    result_dir = repo.create_directory(Path("sub"))
    assert result_dir.is_ok()
    sub_dir = tmp_path / "sub"
    assert sub_dir.exists() and sub_dir.is_dir()

    result_file = repo.create_file(Path("sub/file.txt"))
    assert result_file.is_ok()
    file_path = sub_dir / "file.txt"
    assert file_path.exists()

    result_rm_file = repo.delete_path(Path("sub/file.txt"))
    assert result_rm_file.is_ok()
    assert not file_path.exists()

    result_rm_dir = repo.delete_path(Path("sub"))
    assert result_rm_dir.is_ok()
    assert not sub_dir.exists()
