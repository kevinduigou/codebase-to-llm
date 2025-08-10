from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Column, String, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import (
    FavoritePrompt,
    FavoritePrompts,
)
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_favorite_prompts_table = Table(
    "favorite_prompts",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("content", String, nullable=False),
)


@final
class SqlAlchemyFavoritePromptsRepository(FavoritePromptsRepositoryPort):
    """Favorite prompts repository backed by PostgreSQL."""

    __slots__ = ("_user_id",)
    _user_id: str

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def load_prompts(self) -> Result[FavoritePrompts, str]:
        session = self._session()
        try:
            rows = session.execute(
                _favorite_prompts_table.select().where(
                    _favorite_prompts_table.c.user_id == self._user_id
                )
            ).fetchall()
            prompts: list[FavoritePrompt] = []
            for row in rows:
                prompt_result = FavoritePrompt.try_create(row.id, row.name, row.content)
                if prompt_result.is_err():
                    return Err(prompt_result.err() or "Invalid prompt data.")
                prompt = prompt_result.ok()
                if prompt is None:
                    return Err("Invalid prompt data.")
                prompts.append(prompt)
            prompts_result = FavoritePrompts.try_create(prompts)
            if prompts_result.is_err():
                return Err(prompts_result.err() or "")
            prompts_value = prompts_result.ok()
            assert prompts_value is not None
            return Ok(prompts_value)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def save_prompts(self, prompts: FavoritePrompts) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _favorite_prompts_table.delete().where(
                    _favorite_prompts_table.c.user_id == self._user_id
                )
            )
            for prompt in prompts.prompts():
                session.execute(
                    _favorite_prompts_table.insert().values(
                        id=prompt.id().value(),
                        user_id=self._user_id,
                        name=prompt.name(),
                        content=prompt.content(),
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
