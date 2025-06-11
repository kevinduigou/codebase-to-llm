from pathlib import Path

from domain.directory_tree import build_tree
from domain.result import Ok


def test_tree_build(tmp_path: Path):
    """Quick sanity check on the ASCII tree renderer."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "file.txt").write_text("hello")

    result = build_tree(tmp_path)
    assert isinstance(result, Ok)
    expected_first_line = tmp_path.name
    assert result.ok().splitlines()[0] == expected_first_line  # type: ignore[arg-type,union-attr]
