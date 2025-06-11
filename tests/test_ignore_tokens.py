from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from domain.directory_tree import get_ignore_tokens


def test_override_tokens(tmp_path: Path) -> None:
    tokens = get_ignore_tokens(tmp_path, {"custom"})
    assert "custom" in tokens
