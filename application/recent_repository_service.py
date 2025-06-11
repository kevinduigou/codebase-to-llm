from __future__ import annotations

from pathlib import Path
from typing import Final, List

from domain.result import Result, Ok, Err
from domain.recent_repositories import RecentRepositories
from .ports import RecentRepositoryPort


class RecentRepositoryService:  # noqa: D101
    __slots__ = ("_repo",)

    def __init__(self, repo: RecentRepositoryPort) -> None:
        self._repo: Final = repo

    # -------------------------------------------------------------- queries
    def load_recent(self) -> Result[List[Path], str]:
        return self._repo.load_paths()

    # -------------------------------------------------------------- commands
    def add_path(self, path: Path) -> Result[None, str]:
        current_result = self._repo.load_paths()
        if current_result.is_ok():
            history_result = RecentRepositories.try_create(current_result.ok() or [])
        else:
            history_result = RecentRepositories.try_create([])
        history = history_result.ok()
        if history is None:
            return Err("Failed to load history")
        updated = history.add(path)
        return self._repo.save_paths(list(updated.paths()))
