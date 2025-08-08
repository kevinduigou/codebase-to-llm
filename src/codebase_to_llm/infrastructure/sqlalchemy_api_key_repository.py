from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Column, String, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import ApiKeys, ApiKey, ApiKeyId
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_api_keys_table = Table(
    "api_keys",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("url_provider", String, nullable=False),
    Column("api_key_value", String, nullable=False),
)


@final
class SqlAlchemyApiKeyRepository(ApiKeyRepositoryPort):
    """API key repository backed by PostgreSQL."""

    __slots__ = ("_user_id",)
    _user_id: str

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def load_api_keys(self) -> Result[ApiKeys, str]:
        session = self._session()
        try:
            rows = session.execute(
                _api_keys_table.select().where(
                    _api_keys_table.c.user_id == self._user_id
                )
            ).fetchall()
            keys: list[ApiKey] = []
            for row in rows:
                key_result = ApiKey.try_create(
                    row.id, row.url_provider, row.api_key_value
                )
                if key_result.is_err():
                    return Err(key_result.err() or "Invalid API key data.")
                key = key_result.ok()
                if key is None:
                    return Err("Invalid API key data.")
                keys.append(key)
            api_keys_result = ApiKeys.try_create(tuple(keys))
            if api_keys_result.is_err():
                return Err(api_keys_result.err() or "")
            api_keys = api_keys_result.ok()
            assert api_keys is not None
            return Ok(api_keys)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def save_api_keys(self, api_keys: ApiKeys) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _api_keys_table.delete().where(
                    _api_keys_table.c.user_id == self._user_id
                )
            )
            for api_key in api_keys.api_keys():
                session.execute(
                    _api_keys_table.insert().values(
                        id=api_key.id().value(),
                        user_id=self._user_id,
                        url_provider=api_key.url_provider().value(),
                        api_key_value=api_key.api_key_value().value(),
                    )
                )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def find_api_key_by_id(self, api_key_id: ApiKeyId) -> Result[ApiKey, str]:
        session = self._session()
        try:
            row = session.execute(
                _api_keys_table.select().where(
                    (_api_keys_table.c.user_id == self._user_id)
                    & (_api_keys_table.c.id == api_key_id.value())
                )
            ).fetchone()
            if row is None:
                return Err("API key not found.")
            key_result = ApiKey.try_create(row.id, row.url_provider, row.api_key_value)
            if key_result.is_err():
                return Err(key_result.err() or "Invalid API key data.")
            key = key_result.ok()
            if key is None:
                return Err("Invalid API key data.")
            return Ok(key)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()
