from __future__ import annotations

from pathlib import Path
from typing import Final, List

from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.domain.recent_repositories import RecentRepositories
from .ports import RecentRepositoryPort


class AddPathToRecentRepositoryListUseCase:  # noqa: D101

    def execute(self, path: Path, repo: RecentRepositoryPort) -> Result[None, str]:
        current_result = self._repo.load_paths()
        if current_result.is_ok():
            history_result = RecentRepositories.try_create(current_result.ok() or [])
        else:
            history_result = RecentRepositories.try_create([])
        history = history_result.ok()
        if history is None:
            return Err("Failed to load history")
        updated = history.add(path)
        return repo.save_paths(list(updated.paths()))
