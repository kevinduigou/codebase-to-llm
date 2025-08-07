from __future__ import annotations

from typing_extensions import final
from passlib.context import CryptContext
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.value_object import ValueObject

# Password hashing context using bcrypt
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@final
class UserId(ValueObject):
    """Unique identifier for a user."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["UserId", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("User ID cannot be empty.")
        if len(trimmed_value) > 100:
            return Err("User ID cannot exceed 100 characters.")
        return Ok(UserId(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class UserName(ValueObject):
    """Username used for login."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["UserName", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Username cannot be empty.")
        if len(trimmed_value) > 100:
            return Err("Username cannot exceed 100 characters.")
        return Ok(UserName(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class PasswordHash(ValueObject):
    """Bcrypt hashed password."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def from_plain(password: str) -> "PasswordHash":
        hashed = _pwd_context.hash(password)
        return PasswordHash(hashed)

    @staticmethod
    def try_create(value: str) -> Result["PasswordHash", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Password hash cannot be empty.")
        return Ok(PasswordHash(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value

    def matches(self, password: str) -> bool:
        return _pwd_context.verify(password, self._value)


@final
class User(ValueObject):
    """User entity with immutable fields."""

    __slots__ = ("_id", "_name", "_password_hash")
    _id: UserId
    _name: UserName
    _password_hash: PasswordHash

    @staticmethod
    def try_create(
        id_value: str, name_value: str, password: str
    ) -> Result["User", str]:
        id_result = UserId.try_create(id_value)
        if id_result.is_err():
            return Err(f"Invalid user id: {id_result.err()}")

        name_result = UserName.try_create(name_value)
        if name_result.is_err():
            return Err(f"Invalid username: {name_result.err()}")

        id_obj = id_result.ok()
        name_obj = name_result.ok()
        if id_obj is None or name_obj is None:
            return Err("Unexpected error: one of the value objects is None")

        password_hash = PasswordHash.from_plain(password)
        return Ok(User(id_obj, name_obj, password_hash))

    def __init__(self, id: UserId, name: UserName, password_hash: PasswordHash) -> None:
        self._id = id
        self._name = name
        self._password_hash = password_hash

    def id(self) -> UserId:
        return self._id

    def name(self) -> UserName:
        return self._name

    def password_hash(self) -> PasswordHash:
        return self._password_hash

    def verify_password(self, password: str) -> bool:
        return self._password_hash.matches(password)
