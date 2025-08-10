"""Use case for retrieving rules."""

from __future__ import annotations

from codebase_to_llm.application.ports import RulesRepositoryPort
from codebase_to_llm.domain.rules import Rules
from codebase_to_llm.domain.result import Result


class GetRulesUseCase:
    """Loads the current rules from the repository."""

    def __init__(self, repo: RulesRepositoryPort):
        self._repo = repo

    def execute(self) -> Result[Rules, str]:
        return self._repo.load_rules()
