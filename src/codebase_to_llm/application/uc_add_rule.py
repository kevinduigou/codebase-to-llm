"""Use case for adding a rule."""

from __future__ import annotations

from codebase_to_llm.application.ports import RulesRepositoryPort
from codebase_to_llm.domain.rules import Rule, Rules
from codebase_to_llm.domain.result import Err, Ok, Result


class AddRuleUseCase:
    """Adds a new rule and persists it."""

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
            empty_result = Rules.try_create([])
            if empty_result.is_err():
                return Err(empty_result.err() or "Unknown error creating collection.")
            rules = empty_result.ok()
        else:
            rules = load_result.ok()
            if rules is None:
                empty_result = Rules.try_create([])
                if empty_result.is_err():
                    return Err(
                        empty_result.err() or "Unknown error creating collection."
                    )
                rules = empty_result.ok()

        assert rules is not None
        add_result = rules.add_rule(rule)
        if add_result.is_err():
            return Err(add_result.err() or "Failed to add rule.")
        updated_rules = add_result.ok()
        assert updated_rules is not None

        save_result = self._repo.save_rules(updated_rules)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to save rules.")

        return Ok(rule)
