from __future__ import annotations

from typing import Optional
from typing_extensions import final

from .entity import Entity
from .result import Err, Ok, Result
from .value_object import ValueObject
from .user import UserId
from .directory import DirectoryId


@final
class StoredFileId(ValueObject):
    """Unique identifier for a stored file."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["StoredFileId", str]:
        trimmed = value.strip()
        if not trimmed:
            return Err("File id cannot be empty.")
        return Ok(StoredFileId(trimmed))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class StoredFile(Entity):
    """File metadata owned by a user."""

    __slots__ = ("_owner_id", "_directory_id", "_name")
    _owner_id: UserId
    _directory_id: Optional[DirectoryId]
    _name: str

    @staticmethod
    def try_create(
        id_value: str,
        owner_id: UserId,
        name: str,
        directory_id: Optional[DirectoryId] = None,
    ) -> Result["StoredFile", str]:
        id_result = StoredFileId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid file id.")
        trimmed_name = name.strip()
        if not trimmed_name:
            return Err("File name cannot be empty.")
        id_obj = id_result.ok()
        assert id_obj is not None
        return Ok(StoredFile(id_obj, owner_id, directory_id, trimmed_name))

    def __init__(
        self,
        id: StoredFileId,
        owner_id: UserId,
        directory_id: Optional[DirectoryId],
        name: str,
    ) -> None:
        super().__init__(id)
        self._owner_id = owner_id
        self._directory_id = directory_id
        self._name = name

    def owner_id(self) -> UserId:
        return self._owner_id

    def directory_id(self) -> Optional[DirectoryId]:
        return self._directory_id

    def name(self) -> str:
        return self._name

    def rename(self, new_name: str) -> Result["StoredFile", str]:
        trimmed = new_name.strip()
        if not trimmed:
            return Err("File name cannot be empty.")
        return Ok(StoredFile(self.id(), self._owner_id, self._directory_id, trimmed))

    def move(self, new_directory_id: Optional[DirectoryId]) -> "StoredFile":
        return StoredFile(self.id(), self._owner_id, new_directory_id, self._name)
