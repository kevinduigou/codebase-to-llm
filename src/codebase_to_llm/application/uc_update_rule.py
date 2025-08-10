"""Use case for updating an existing rule."""

from __future__ import annotations

from codebase_to_llm.application.ports import RulesRepositoryPort
from codebase_to_llm.domain.rules import Rule
from codebase_to_llm.domain.result import Err, Ok, Result


class UpdateRuleUseCase:
    """Updates a rule identified by its name."""

    def __init__(self, repo: RulesRepositoryPort):
        self._repo = repo

    def execute(
        self,
        name: str,
        content: str,
        description: str | None = None,
        enabled: bool = True,
    ) -> Result[Rule, str]:
        rule_result = Rule.try_create(name, content, description, enabled)
        if rule_result.is_err():
            return Err(rule_result.err() or "Failed to create rule.")
        rule = rule_result.ok()
        if rule is None:
            return Err("Failed to create rule.")

        load_result = self._repo.load_rules()
        if load_result.is_err():
            return Err(load_result.err() or "Failed to load rules.")
        rules = load_result.ok()
        if rules is None:
            return Err("Failed to load rules.")

        update_result = rules.update_rule(rule)
        if update_result.is_err():
            return Err(update_result.err() or "Failed to update rule.")
        updated_rules = update_result.ok()
        assert updated_rules is not None

        save_result = self._repo.save_rules(updated_rules)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save rules.")

        return Ok(rule)
