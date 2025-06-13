from __future__ import annotations

from pathlib import Path
from typing import Final

from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.application.ports import RulesRepositoryPort


class FileSystemRulesRepository(RulesRepositoryPort):
    """Reads / writes the rules text in the user’s home directory."""

    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None):
        default_path = Path.home() / ".copy_to_llm" / "rules"
        self._path: Final = path or default_path

    # -------------------------------------------------------------- public API
    def load_rules(self) -> Result[str, str]:
        try:  # I/O happens in infra, so a *try* is acceptable here
            if not self._path.exists():
                return Err("Rules file not found.")
            raw = self._path.read_text(encoding="utf-8", errors="ignore")
            return Ok(raw)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def save_rules(self, rules: str) -> Result[None, str]:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(rules, encoding="utf-8")
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
