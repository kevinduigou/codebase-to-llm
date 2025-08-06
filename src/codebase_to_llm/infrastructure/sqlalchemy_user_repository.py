from __future__ import annotations

from typing_extensions import final
from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import PasswordHash, User, UserId, UserName
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_engine

_metadata = MetaData()

_users_table = Table(
    "users",
    _metadata,
    Column("id", String, primary_key=True),
    Column("name", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
)

_metadata.create_all(get_engine())


@final
class SqlAlchemyUserRepository(UserRepositoryPort):
    """User repository backed by SQLAlchemy."""

    __slots__ = ()

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def add_user(self, user: User) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _users_table.insert().values(
                    id=user.id().value(),
                    name=user.name().value(),
                    password_hash=user.password_hash().value(),
                )
            )
            session.commit()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            return Err(str(exc))

    def find_by_name(self, name: UserName) -> Result[User, str]:
        session = self._session()
        try:
            row = session.execute(
                _users_table.select().where(_users_table.c.name == name.value())
            ).fetchone()
            if row is None:
                return Err("User not found.")

            id_result = UserId.try_create(row.id)
            name_result = UserName.try_create(row.name)
            hash_result = PasswordHash.try_create(row.password_hash)
            if id_result.is_err() or name_result.is_err() or hash_result.is_err():
                return Err("Invalid user data.")

            id_obj = id_result.ok()
            name_obj = name_result.ok()
            hash_obj = hash_result.ok()
            if id_obj is None or name_obj is None or hash_obj is None:
                return Err("Invalid user data.")

            return Ok(User(id_obj, name_obj, hash_obj))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
