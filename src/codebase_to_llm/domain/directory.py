from __future__ import annotations

from typing import Optional
from typing_extensions import final

from .entity import Entity
from .result import Err, Ok, Result
from .value_object import ValueObject
from .user import UserId


@final
class DirectoryId(ValueObject):
    """Unique identifier for a directory."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["DirectoryId", str]:
        trimmed = value.strip()
        if not trimmed:
            return Err("Directory id cannot be empty.")
        return Ok(DirectoryId(trimmed))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class Directory(Entity):
    """Directory owned by a user."""

    __slots__ = ("_owner_id", "_parent_id", "_name")
    _owner_id: UserId
    _parent_id: Optional[DirectoryId]
    _name: str

    @staticmethod
    def try_create(
        id_value: str,
        owner_id: UserId,
        name: str,
        parent_id: Optional[DirectoryId] = None,
    ) -> Result["Directory", str]:
        id_result = DirectoryId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid directory id.")
        trimmed_name = name.strip()
        if not trimmed_name:
            return Err("Directory name cannot be empty.")
        id_obj = id_result.ok()
        assert id_obj is not None
        return Ok(Directory(id_obj, owner_id, parent_id, trimmed_name))

    def __init__(
        self,
        id: DirectoryId,
        owner_id: UserId,
        parent_id: Optional[DirectoryId],
        name: str,
    ) -> None:
        super().__init__(id)
        self._owner_id = owner_id
        self._parent_id = parent_id
        self._name = name

    def owner_id(self) -> UserId:
        return self._owner_id

    def parent_id(self) -> Optional[DirectoryId]:
        return self._parent_id

    def name(self) -> str:
        return self._name

    def rename(self, new_name: str) -> Result["Directory", str]:
        trimmed = new_name.strip()
        if not trimmed:
            return Err("Directory name cannot be empty.")
        return Ok(Directory(self.id(), self._owner_id, self._parent_id, trimmed))

    def move(self, new_parent_id: Optional[DirectoryId]) -> "Directory":
        return Directory(self.id(), self._owner_id, new_parent_id, self._name)
