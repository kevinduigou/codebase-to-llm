from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from application.copy_context import CopyContextUseCase
from infrastructure.filesystem_directory_repository import FileSystemDirectoryRepository


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
    use_case.execute([], include_tree=True)
    assert clipboard.text is not None
    assert "<tree_structure>" in clipboard.text
    clipboard2 = FakeClipboard()
    use_case2 = CopyContextUseCase(repo, clipboard2)
    use_case2.execute([], include_tree=False)
    assert clipboard2.text is not None
    assert "<tree_structure>" not in clipboard2.text
