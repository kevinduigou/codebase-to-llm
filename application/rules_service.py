from __future__ import annotations

from typing import Final

from domain.result import Result, Err, Ok
from domain.rules import Rules
from .ports import RulesRepositoryPort


class RulesService:  # noqa: D101
    __slots__ = ("_repo",)

    def __init__(self, repo: RulesRepositoryPort):
        self._repo: Final = repo

    # -------------------------------------------------------------- queries
    def load_rules(self) -> Result[str, str]:
        """Load persisted rules text (may return Err if absent or unreadable)."""
        return self._repo.load_rules()

    # -------------------------------------------------------------- commands
    def save_rules(self, raw_text: str) -> Result[None, str]:
        rules_result = Rules.try_create(raw_text)
        if rules_result.is_err():
            # Propagate the domain-level validation error
            return Err(rules_result.err())  # type: ignore[arg-type]
        rules = rules_result.ok()
        if rules is None:
            return Err("Failed to create rules object.")
        return self._repo.save_rules(rules.text())
