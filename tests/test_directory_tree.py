from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from codebase_to_llm.domain.directory_tree import build_tree
from codebase_to_llm.domain.result import Ok


def test_tree_build(tmp_path: Path):
    """Quick sanity check on the ASCII tree renderer."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "file.txt").write_text("hello")

    result = build_tree(tmp_path)
    assert isinstance(result, Ok)
    expected_first_line = tmp_path.name
    assert result.ok().splitlines()[0] == expected_first_line  # type: ignore[arg-type,union-attr]
