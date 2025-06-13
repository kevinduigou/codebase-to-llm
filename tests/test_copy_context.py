from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from application.copy_context import CopyContextUseCase
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository
from domain.selected_text import SelectedText


class FakeClipboard:
    def __init__(self) -> None:
        self.text: str | None = None

    def set_text(self, text: str) -> None:
        self.text = text


def test_include_tree_flag(tmp_path: Path):
    (tmp_path / "file.txt").write_text("hello")
    repo = FileSystemDirectoryRepository(tmp_path)
    clipboard = FakeClipboard()
    use_case = CopyContextUseCase(repo, clipboard)
    use_case.execute([], [], include_tree=True)
    assert clipboard.text is not None
    assert "<tree_structure>" in clipboard.text
    clipboard2 = FakeClipboard()
    use_case2 = CopyContextUseCase(repo, clipboard2)
    use_case2.execute([], [], include_tree=False)
    assert clipboard2.text is not None
    assert "<tree_structure>" not in clipboard2.text


def test_selected_text(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("line1\nline2\nline3\n")
    repo = FileSystemDirectoryRepository(tmp_path)
    clipboard = FakeClipboard()
    use_case = CopyContextUseCase(repo, clipboard)
    snippet_result = SelectedText.try_create(file_path, 1, 2, "line1\nline2\n")
    assert snippet_result.is_ok()
    snippet = snippet_result.ok()
    use_case.execute([], [snippet], include_tree=False)
    assert clipboard.text is not None
    expected_tag = f"<{file_path}:1:2>"
    assert expected_tag in clipboard.text
    assert "line1" in clipboard.text
