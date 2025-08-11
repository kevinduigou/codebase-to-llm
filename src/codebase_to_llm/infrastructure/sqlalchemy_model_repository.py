from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Column, String, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from codebase_to_llm.application.ports import ModelRepositoryPort
from codebase_to_llm.domain.model import Models, Model, ModelId
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_models_table = Table(
    "models",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("api_key_id", String, nullable=False),
)


@final
class SqlAlchemyModelRepository(ModelRepositoryPort):
    """Model repository backed by PostgreSQL."""

    __slots__ = ("_user_id",)
    _user_id: str

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def load_models(self) -> Result[Models, str]:
        session = self._session()
        try:
            rows = session.execute(
                _models_table.select().where(_models_table.c.user_id == self._user_id)
            ).fetchall()
            models_list: list[Model] = []
            for row in rows:
                model_result = Model.try_create(
                    row.id,
                    row.user_id,
                    row.name,
                    row.api_key_id,
                )
                if model_result.is_err():
                    return Err(model_result.err() or "Invalid model data.")
                model = model_result.ok()
                if model is None:
                    return Err("Invalid model data.")
                models_list.append(model)
            models_result = Models.try_create(tuple(models_list))
            if models_result.is_err():
                return Err(models_result.err() or "")
            models = models_result.ok()
            assert models is not None
            return Ok(models)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def save_models(self, models: Models) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _models_table.delete().where(_models_table.c.user_id == self._user_id)
            )
            for model in models.models():
                session.execute(
                    _models_table.insert().values(
                        id=model.id().value(),
                        user_id=self._user_id,
                        name=model.name().value(),
                        api_key_id=model.api_key_id().value(),
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

    def find_model_by_id(self, model_id: ModelId) -> Result[Model, str]:
        session = self._session()
        try:
            row = session.execute(
                _models_table.select().where(
                    (_models_table.c.user_id == self._user_id)
                    & (_models_table.c.id == model_id.value())
                )
            ).fetchone()
            if row is None:
                return Err("Model not found.")
            model_result = Model.try_create(
                row.id,
                row.user_id,
                row.name,
                row.api_key_id,
            )
            if model_result.is_err():
                return Err(model_result.err() or "Invalid model data.")
            model = model_result.ok()
            if model is None:
                return Err("Invalid model data.")
            return Ok(model)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()
