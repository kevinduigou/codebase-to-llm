from __future__ import annotations

from typing import Iterable, Tuple
from typing_extensions import final

from codebase_to_llm.domain.value_object import ValueObject

from .result import Result, Ok, Err


@final
class Rule:
    """Single rule with a mandatory name and optional description."""

    __slots__ = ("_name", "_content", "_description", "_enabled")

    _name: str
    _description: str | None
    _content: str
    _enabled: bool

    @staticmethod
    def try_create(
        name: str, _content: str, description: str | None = None, enabled: bool = True
    ) -> Result["Rule", str]:
        trimmed_name = name.strip()
        if not trimmed_name:
            return Err("Rule name cannot be empty.")
        desc = description.strip() if description else None
        return Ok(Rule(trimmed_name, _content, desc, enabled))

    def __init__(
        self, name: str, content: str, description: str | None, enabled: bool = True
    ) -> None:
        self._name = name
        self._description = description
        self._content = content
        self._enabled = enabled

    def name(self) -> str:
        return self._name

    def description(self) -> str | None:
        return self._description

    def content(self) -> str:
        return self._content

    def enabled(self) -> bool:
        return self._enabled

    def update_enabled(self, enabled: bool) -> "Rule":
        return Rule(self._name, self._content, self._description, enabled)


@final
class Rules(ValueObject):
    """Immutable collection of :class:`Rule` objects."""

    __slots__ = ("_rules",)
    _rules: Tuple[Rule, ...]

    # ----------------------------------------------------------------- factory
    @staticmethod
    def try_create(rules: Iterable[Rule]) -> Result["Rules", str]:
        return Ok(Rules(tuple(rules)))

    # ----------------------------------------------------------------- ctor (kept private – do not call directly)
    def __init__(self, rules: Tuple[Rule, ...]):
        self._rules = rules

    # ----------------------------------------------------------------- accessors
    def rules(self) -> Tuple[Rule, ...]:  # noqa: D401
        return self._rules

    def to_text(self) -> str:
        parts = []
        for r in self._rules:
            if r.description():
                parts.append(f"{r.name()}: {r.description()}")
            else:
                parts.append(r.name())
        return "\n".join(parts)

    def add_rule(self, rule: Rule) -> Result["Rules", str]:
        for existing in self._rules:
            if existing.name() == rule.name():
                return Err(f'Rule with name "{rule.name()}" already exists.')
        return Ok(Rules(self._rules + (rule,)))

    def update_rule(self, rule: Rule) -> Result["Rules", str]:
        new_rules = []
        found = False
        for existing in self._rules:
            if existing.name() == rule.name():
                new_rules.append(rule)
                found = True
            else:
                new_rules.append(existing)
        if not found:
            return Err(f'Rule with name "{rule.name()}" not found.')
        return Ok(Rules(tuple(new_rules)))

    def update_rule_enabled(self, name: str, enabled: bool) -> "Rules":
        new_rules: tuple[Rule, ...] = tuple()
        for rule in self._rules:
            if rule.name() == name:
                new_rules = new_rules + (rule.update_enabled(enabled),)
            else:
                new_rules = new_rules + (rule,)
        return Rules(new_rules)

    def remove_rule(self, name: str) -> "Rules":
        new_rules: tuple[Rule, ...] = tuple()
        for rule in self._rules:
            if rule.name() == name:
                new_rules = new_rules
            else:
                new_rules = new_rules + (rule,)
        return Rules(new_rules)
