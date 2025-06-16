from __future__ import annotations

from typing import Iterable, Tuple
from typing_extensions import final

from codebase_to_llm.domain.value_object import ValueObject

from .result import Result, Ok, Err


@final
class Rule(ValueObject):
    """Single rule with a mandatory name and optional description."""

    __slots__ = ("_name", "_description")

    _name: str
    _description: str | None

    @staticmethod
    def try_create(name: str, description: str | None = None) -> Result["Rule", str]:
        trimmed = name.strip()
        if not trimmed:
            return Err("Rule name cannot be empty.")
        desc = description.strip() if description else None
        return Ok(Rule(trimmed, desc))

    def __init__(self, name: str, description: str | None) -> None:
        self._name = name
        self._description = description

    def name(self) -> str:
        return self._name

    def description(self) -> str | None:
        return self._description


@final
class Rules(ValueObject):
    """Immutable collection of :class:`Rule` objects."""

    __slots__ = ("_rules",)
    _rules: Tuple[Rule, ...]

    # ----------------------------------------------------------------- factory
    @staticmethod
    def try_create(rules: Iterable[Rule]) -> Result["Rules", str]:
        return Ok(Rules(tuple(rules)))

    @staticmethod
    def try_from_text(text: str) -> Result["Rules", str]:
        items: list[Rule] = []
        for line in [ln.strip() for ln in text.splitlines() if ln.strip()]:
            if ":" in line:
                name, desc = line.split(":", 1)
                rule_result = Rule.try_create(name.strip(), desc.strip())
            else:
                rule_result = Rule.try_create(line, None)
            if rule_result.is_err():
                return Err(rule_result.err())
            rule = rule_result.ok()
            assert rule is not None
            items.append(rule)
        return Ok(Rules(tuple(items)))

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
