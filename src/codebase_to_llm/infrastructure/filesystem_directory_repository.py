from __future__ import annotations

from pathlib import Path
from typing import Final
import shutil

from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.directory_tree import build_tree as domain_build_tree

from codebase_to_llm.application.ports import DirectoryRepositoryPort


class FileSystemDirectoryRepository(DirectoryRepositoryPort):
    """Pure‐query adapter over the local file‑system (read‑only)."""

    __slots__ = ("_root",)

    def __init__(self, root: Path):
        self._root: Final = root

    def build_tree(self) -> Result[str, str]:  # noqa: D401 (simple verb)
        return domain_build_tree(self._root)

    def read_file(
        self, relative_path: Path
    ) -> Result[str, str]:  # noqa: D401 (simple verb)
        full_path = (self._root / relative_path).resolve()
        if not full_path.exists() or not full_path.is_file():
            return Err(f"File not found: {relative_path}")
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            return Ok(content)
        except Exception as exc:  # noqa: BLE001 (broad exc) – external edge
            # NOTE: This `try` is inside infrastructure, which may legitimately deal
            #       with unpredictable I/O. Domain & application layers remain pure.
            return Err(str(exc))

    def create_file(self, relative_path: Path) -> Result[None, str]:  # noqa: D401
        full_path = (self._root / relative_path).resolve()
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch(exist_ok=False)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def create_directory(self, relative_path: Path) -> Result[None, str]:  # noqa: D401
        full_path = (self._root / relative_path).resolve()
        try:
            full_path.mkdir(parents=True, exist_ok=False)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def delete_path(self, relative_path: Path) -> Result[None, str]:  # noqa: D401
        full_path = (self._root / relative_path).resolve()
        try:
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink(missing_ok=True)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
