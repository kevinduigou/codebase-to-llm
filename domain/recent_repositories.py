from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple, Final

from typing_extensions import final

from .value_object import ValueObject
from .result import Result, Ok, Err

MAX_HISTORY: Final[int] = 10


@final
class RecentRepositories(ValueObject):
    """Immutable list of recently opened repository paths."""

    __slots__ = ("_paths",)
    _paths: Tuple[Path, ...]

    # --------------------------------------------------------------------- factory
    @staticmethod
    def try_create(paths: Iterable[Path]) -> Result["RecentRepositories", str]:
        unique: List[Path] = []
        for path in paths:
            if path not in unique:
                unique.append(path)
        if len(unique) > MAX_HISTORY:
            unique = unique[:MAX_HISTORY]
        return Ok(RecentRepositories(tuple(unique)))

    # --------------------------------------------------------------------- ctor
    def __init__(self, paths: Tuple[Path, ...]):
        self._paths = paths

    # --------------------------------------------------------------------- accessors
    def paths(self) -> Tuple[Path, ...]:  # noqa: D401
        return self._paths

    # --------------------------------------------------------------------- operations
    def add(self, path: Path) -> "RecentRepositories":
        """Return a new object with ``path`` added to the history."""
        new_paths = [p for p in self._paths if p != path]
        new_paths.insert(0, path)
        if len(new_paths) > MAX_HISTORY:
            new_paths = new_paths[:MAX_HISTORY]
        return RecentRepositories(tuple(new_paths))
