from __future__ import annotations

from pathlib import Path
from typing import Final, List

from domain.result import Result, Ok, Err
from application.ports import IgnoreRepositoryPort


class FileSystemIgnoreRepository(IgnoreRepositoryPort):
    """Persist ignore tokens on disk."""

    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None) -> None:
        default_path = Path.home() / ".copy_to_llm" / "ignores"
        self._path: Final = path or default_path

    def load_tokens(self) -> Result[List[str], str]:  # noqa: D401
        try:
            if not self._path.exists():
                return Ok([])
            raw = self._path.read_text(encoding="utf-8", errors="ignore")
            lines = [line for line in raw.splitlines() if line.strip()]
            return Ok(lines)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def save_tokens(self, tokens: List[str]) -> Result[None, str]:  # noqa: D401
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            content = "\n".join(tokens)
            self._path.write_text(content, encoding="utf-8")
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
