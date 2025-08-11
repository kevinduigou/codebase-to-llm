from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Column, String, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import DirectoryStructureRepositoryPort
from codebase_to_llm.domain.directory import Directory, DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_directories_table = Table(
    "directories",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("parent_id", String, nullable=True),
    Column("name", String, nullable=False),
)


@final
class SqlAlchemyDirectoryRepository(DirectoryStructureRepositoryPort):
    """Directory repository backed by PostgreSQL."""

    __slots__ = ()

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def add(self, directory: Directory) -> Result[None, str]:
        session = self._session()
        try:
            parent = directory.parent_id()
            session.execute(
                _directories_table.insert().values(
                    id=directory.id().value(),
                    user_id=directory.owner_id().value(),
                    parent_id=parent.value() if parent is not None else None,
                    name=directory.name(),
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def get(self, directory_id: DirectoryId) -> Result[Directory, str]:
        session = self._session()
        try:
            row = session.execute(
                _directories_table.select().where(
                    _directories_table.c.id == directory_id.value()
                )
            ).fetchone()
            if row is None:
                return Err("Directory not found")
            owner_res = UserId.try_create(row.user_id)
            if owner_res.is_err():
                return Err("Invalid user id in database")
            owner_id = owner_res.ok()
            assert owner_id is not None
            parent_id = None
            if row.parent_id is not None:
                parent_res = DirectoryId.try_create(row.parent_id)
                if parent_res.is_err():
                    return Err("Invalid parent id in database")
                parent_id = parent_res.ok()
                assert parent_id is not None
            dir_res = Directory.try_create(row.id, owner_id, row.name, parent_id)
            if dir_res.is_err():
                return Err(dir_res.err() or "Invalid directory data")
            directory = dir_res.ok()
            assert directory is not None
            return Ok(directory)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))

    def update(self, directory: Directory) -> Result[None, str]:
        session = self._session()
        try:
            parent = directory.parent_id()
            session.execute(
                _directories_table.update()
                .where(_directories_table.c.id == directory.id().value())
                .values(
                    user_id=directory.owner_id().value(),
                    parent_id=parent.value() if parent is not None else None,
                    name=directory.name(),
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def remove(self, directory_id: DirectoryId) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _directories_table.delete().where(
                    _directories_table.c.id == directory_id.value()
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
