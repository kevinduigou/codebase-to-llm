from __future__ import annotations

import logging
from pathlib import Path
from typing import List
from typing_extensions import final
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from codebase_to_llm.application.ports import RecentRepositoryPort
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_recent_repos_table = Table(
    "recent_repos",
    get_metadata(),
    Column("user_id", String, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("path", String, nullable=False),
)


@final
class SqlAlchemyRecentRepository(RecentRepositoryPort):
    """Recent repositories backed by PostgreSQL."""

    __slots__ = ("_user_id",)
    _user_id: str

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def load_paths(self) -> Result[List[Path], str]:
        session = self._session()
        try:
            rows = session.execute(
                _recent_repos_table.select()
                .where(_recent_repos_table.c.user_id == self._user_id)
                .order_by(_recent_repos_table.c.position)
            ).fetchall()
            paths = [Path(row.path) for row in rows]
            return Ok(paths)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))

    def save_paths(self, paths: List[Path]) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _recent_repos_table.delete().where(
                    _recent_repos_table.c.user_id == self._user_id
                )
            )
            for position, path in enumerate(paths):
                session.execute(
                    _recent_repos_table.insert().values(
                        user_id=self._user_id,
                        position=position,
                        path=str(path),
                    )
                )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def get_latest_repo(self) -> Result[Path, str]:
        session = self._session()
        try:
            row = session.execute(
                _recent_repos_table.select().where(
                    (_recent_repos_table.c.user_id == self._user_id)
                    & (_recent_repos_table.c.position == 0)
                )
            ).fetchone()
            if row is None:
                return Err("No recent repos found")
            return Ok(Path(row.path))
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
