"""Use case for removing a rule."""

from __future__ import annotations

from codebase_to_llm.application.ports import RulesRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result


class RemoveRuleUseCase:
    """Removes a rule identified by its name."""

    def __init__(self, repo: RulesRepositoryPort):
        self._repo = repo

    def execute(self, name: str) -> Result[None, str]:
        load_result = self._repo.load_rules()
        if load_result.is_err():
            return Err(load_result.err() or "Failed to load rules.")
        rules = load_result.ok()
        if rules is None:
            return Err("Failed to load rules.")

        before = len(rules.rules())
        new_rules = rules.remove_rule(name)
        after = len(new_rules.rules())
        if before == after:
            return Err(f'Rule with name "{name}" not found.')

        save_result = self._repo.save_rules(new_rules)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save rules.")

        return Ok(None)
