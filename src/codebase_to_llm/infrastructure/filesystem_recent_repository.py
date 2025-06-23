from __future__ import annotations

import json
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
            data = json.loads(raw)
            paths = [Path(p) for p in data.get("paths", [])]
            return Ok(paths)
        except Exception as exc:  # noqa: BLE001
            return Err(
                f"Corrupted files, please delete the file and try again! {self._path} {str(exc)}"
            )

    def save_paths(
        self, latest_repo: Path, paths: List[Path]
    ) -> Result[None, str]:  # noqa: D401
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            latest_repo = str(paths[0]) if paths else None
            data = {
                "latest_repo": latest_repo,
                "paths": [str(p) for p in paths],
            }
            content = json.dumps(data, indent=2)
            self._path.write_text(content, encoding="utf-8")
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def get_latest_repo(self) -> Result[Path, str]:  # noqa: D401
        try:
            if not self._path.exists():
                return Err("No recent repos found")
            raw = self._path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(raw)
            return Ok(Path(data.get("latest_repo", "")))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
