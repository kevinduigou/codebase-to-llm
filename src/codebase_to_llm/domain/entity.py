from __future__ import annotations

from typing import Any


class Entity:
    """Base class for entities compared by identity."""

    __slots__ = ("_id",)
    _id: Any

    def __init__(self, id: Any) -> None:
        self._id = id

    def id(self) -> Any:
        return self._id

    def __eq__(self, other: object) -> bool:  # noqa: D401 - simple verb
        return isinstance(other, Entity) and self._id == other._id

    def __hash__(self) -> int:  # noqa: D401 - simple verb
        return hash(self._id)
