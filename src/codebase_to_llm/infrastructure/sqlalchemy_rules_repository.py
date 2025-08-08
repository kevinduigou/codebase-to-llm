from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Boolean, Column, String, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from codebase_to_llm.application.ports import RulesRepositoryPort
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.domain.rules import Rule, Rules
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_rules_table = Table(
    "rules",
    get_metadata(),
    Column("user_id", String, primary_key=True),
    Column("name", String, primary_key=True),
    Column("content", String, nullable=False),
    Column("description", String),
    Column("enabled", Boolean, nullable=False),
)


@final
class SqlAlchemyRulesRepository(RulesRepositoryPort):
    """Rules repository backed by PostgreSQL."""

    __slots__ = ("_user_id",)
    _user_id: str

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def load_rules(self) -> Result[Rules, str]:
        session = self._session()
        try:
            rows = session.execute(
                _rules_table.select().where(_rules_table.c.user_id == self._user_id)
            ).fetchall()
            rules: list[Rule] = []
            for row in rows:
                rule_result = Rule.try_create(
                    row.name, row.content, row.description, row.enabled
                )
                if rule_result.is_err():
                    return Err(rule_result.err() or "Invalid rule data.")
                rule = rule_result.ok()
                if rule is None:
                    return Err("Invalid rule data.")
                rules.append(rule)
            rules_result = Rules.try_create(rules)
            if rules_result.is_err():
                return Err(rules_result.err() or "")
            rules_value = rules_result.ok()
            assert rules_value is not None
            return Ok(rules_value)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))

    def save_rules(self, rules: Rules) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _rules_table.delete().where(_rules_table.c.user_id == self._user_id)
            )
            for rule in rules.rules():
                session.execute(
                    _rules_table.insert().values(
                        user_id=self._user_id,
                        name=rule.name(),
                        content=rule.content(),
                        description=rule.description(),
                        enabled=rule.enabled(),
                    )
                )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def update_rule_enabled(self, name: str, enabled: bool) -> Result[None, str]:
        session = self._session()
        try:
            result = session.execute(
                _rules_table.update()
                .where(
                    (_rules_table.c.user_id == self._user_id)
                    & (_rules_table.c.name == name)
                )
                .values(enabled=enabled)
            )
            if result.rowcount == 0:
                session.rollback()
                return Err("Rule not found")
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
