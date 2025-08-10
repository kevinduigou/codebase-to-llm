from __future__ import annotations
import logging

from typing_extensions import final
from sqlalchemy import Boolean, Column, String, Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import (
    EmailAddress,
    PasswordHash,
    User,
    UserId,
    UserName,
    ValidationToken,
)
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_users_table = Table(
    "users",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("name", String, unique=True, nullable=False),
    Column("email", String, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("validated", Boolean, nullable=False),
    Column("validation_token", String, nullable=False),
)


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
                    email=user.email().value(),
                    password_hash=user.password_hash().value(),
                    validated=user.is_validated(),
                    validation_token=user.validation_token().value(),
                )
            )
            session.commit()
            return Ok(None)
        except IntegrityError as exc:
            session.rollback()
            logging.warning(str(exc))
            # Check if it's a UNIQUE constraint violation on the name field
            if "UNIQUE constraint failed: users.name" in str(exc):
                return Err("User already exist")
            return Err(str(exc))
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

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
            email_result = EmailAddress.try_create(row.email)
            hash_result = PasswordHash.try_create(row.password_hash)
            token_result = ValidationToken.try_create(row.validation_token)
            if (
                id_result.is_err()
                or name_result.is_err()
                or hash_result.is_err()
            ):
                return Err("Invalid user data.")

            id_obj = id_result.ok()
            name_obj = name_result.ok()
            email_obj = email_result.ok()
            hash_obj = hash_result.ok()
            token_obj = token_result.ok()
            if (
                id_obj is None
                or name_obj is None
                or hash_obj is None
            ):
                return Err("Invalid user data.")

            return Ok(
                User(
                    id_obj,
                    name_obj,
                    email_obj,
                    hash_obj,
                    bool(row.validated),
                    token_obj,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def find_by_email(self, email: EmailAddress) -> Result[User, str]:
        session = self._session()
        try:
            row = session.execute(
                _users_table.select().where(_users_table.c.email == email.value())
            ).fetchone()
            if row is None:
                return Err("User not found.")
            id_result = UserId.try_create(row.id)
            name_result = UserName.try_create(row.name)
            email_result = EmailAddress.try_create(row.email)
            hash_result = PasswordHash.try_create(row.password_hash)
            token_result = ValidationToken.try_create(row.validation_token)
            if (
                id_result.is_err()
                or name_result.is_err()
                or email_result.is_err()
                or hash_result.is_err()
                or token_result.is_err()
            ):
                return Err("Invalid user data.")

            id_obj = id_result.ok()
            name_obj = name_result.ok()
            email_obj = email_result.ok()
            hash_obj = hash_result.ok()
            token_obj = token_result.ok()
            if (
                id_obj is None
                or name_obj is None
                or email_obj is None
                or hash_obj is None
                or token_obj is None
            ):
                return Err("Invalid user data.")

            return Ok(
                User(
                    id_obj,
                    name_obj,
                    email_obj,
                    hash_obj,
                    bool(row.validated),
                    token_obj,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def find_by_validation_token(self, token: ValidationToken) -> Result[User, str]:
        session = self._session()
        try:
            row = session.execute(
                _users_table.select().where(
                    _users_table.c.validation_token == token.value()
                )
            ).fetchone()
            if row is None:
                return Err("User not found.")

            id_result = UserId.try_create(row.id)
            name_result = UserName.try_create(row.name)
            email_result = EmailAddress.try_create(row.email)
            hash_result = PasswordHash.try_create(row.password_hash)
            token_result = ValidationToken.try_create(row.validation_token)
            if (
                id_result.is_err()
                or name_result.is_err()
                or email_result.is_err()
                or hash_result.is_err()
                or token_result.is_err()
            ):
                return Err("Invalid user data.")

            id_obj = id_result.ok()
            name_obj = name_result.ok()
            email_obj = email_result.ok()
            hash_obj = hash_result.ok()
            token_obj = token_result.ok()
            if (
                id_obj is None
                or name_obj is None
                or email_obj is None
                or hash_obj is None
                or token_obj is None
            ):
                return Err("Invalid user data.")

            return Ok(
                User(
                    id_obj,
                    name_obj,
                    email_obj,
                    hash_obj,
                    bool(row.validated),
                    token_obj,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def validate_user(self, user: User) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _users_table.update()
                .where(_users_table.c.id == user.id().value())
                .values(validated=True)
            )
            session.commit()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()
