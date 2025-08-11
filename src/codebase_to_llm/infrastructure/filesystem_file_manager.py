from __future__ import annotations

import shutil
from pathlib import Path

from codebase_to_llm.application.ports import FileSystemPort
from codebase_to_llm.domain.result import Err, Ok, Result


class FileSystemFileManager(FileSystemPort):
    """Adapter performing mutations on the local file system."""

    __slots__ = ()

    def create_file(self, parent: Path, name: str) -> Result[None, str]:
        try:
            (parent / name).touch(exist_ok=False)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def create_folder(self, parent: Path, name: str) -> Result[None, str]:
        try:
            (parent / name).mkdir(exist_ok=False)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def delete_path(self, path: Path) -> Result[None, str]:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def rename_path(self, path: Path, new_name: str) -> Result[None, str]:
        try:
            path.rename(path.parent / new_name)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
