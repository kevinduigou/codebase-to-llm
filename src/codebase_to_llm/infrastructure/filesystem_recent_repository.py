from __future__ import annotations

from pathlib import Path
from typing import Final, List

from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.application.ports import RecentRepositoryPort


class FileSystemRecentRepository(RecentRepositoryPort):
    """Persists the list of recently opened repositories on disk."""

    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None) -> None:
        default_path = Path.home() / ".copy_to_llm" / "recent_repos"
        self._path: Final = path or default_path

    def load_paths(self) -> Result[List[Path], str]:  # noqa: D401
        try:
            if not self._path.exists():
                return Ok([])
            raw = self._path.read_text(encoding="utf-8", errors="ignore")
            lines = [Path(line) for line in raw.splitlines() if line.strip()]
            return Ok(lines)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def save_paths(self, paths: List[Path]) -> Result[None, str]:  # noqa: D401
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            content = "\n".join(str(p) for p in paths)
            self._path.write_text(content, encoding="utf-8")
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
