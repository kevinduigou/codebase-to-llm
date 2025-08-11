from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Column, String, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import FileRepositoryPort
from codebase_to_llm.domain.stored_file import StoredFile, StoredFileId
from codebase_to_llm.domain.directory import DirectoryId
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_files_table = Table(
    "files",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("directory_id", String, nullable=True),
    Column("name", String, nullable=False),
)


@final
class SqlAlchemyFileRepository(FileRepositoryPort):
    """File metadata repository backed by PostgreSQL."""

    __slots__ = ()

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def add(self, file: StoredFile) -> Result[None, str]:
        session = self._session()
        try:
            dir_id = file.directory_id()
            session.execute(
                _files_table.insert().values(
                    id=file.id().value(),
                    user_id=file.owner_id().value(),
                    directory_id=dir_id.value() if dir_id is not None else None,
                    name=file.name(),
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def get(self, file_id: StoredFileId) -> Result[StoredFile, str]:
        session = self._session()
        try:
            row = session.execute(
                _files_table.select().where(_files_table.c.id == file_id.value())
            ).fetchone()
            if row is None:
                return Err("File not found")
            owner_res = UserId.try_create(row.user_id)
            if owner_res.is_err():
                return Err("Invalid user id in database")
            owner_id = owner_res.ok()
            assert owner_id is not None
            directory_id = None
            if row.directory_id is not None:
                dir_res = DirectoryId.try_create(row.directory_id)
                if dir_res.is_err():
                    return Err("Invalid directory id in database")
                directory_id = dir_res.ok()
                assert directory_id is not None
            file_res = StoredFile.try_create(row.id, owner_id, row.name, directory_id)
            if file_res.is_err():
                return Err(file_res.err() or "Invalid file data")
            file = file_res.ok()
            assert file is not None
            return Ok(file)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))

    def update(self, file: StoredFile) -> Result[None, str]:
        session = self._session()
        try:
            dir_id = file.directory_id()
            session.execute(
                _files_table.update()
                .where(_files_table.c.id == file.id().value())
                .values(
                    user_id=file.owner_id().value(),
                    directory_id=dir_id.value() if dir_id is not None else None,
                    name=file.name(),
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def remove(self, file_id: StoredFileId) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _files_table.delete().where(_files_table.c.id == file_id.value())
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
