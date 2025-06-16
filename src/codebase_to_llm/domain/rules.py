from __future__ import annotations

from typing import Iterable, Tuple
from typing_extensions import final

from codebase_to_llm.domain.value_object import ValueObject

from .result import Result, Ok, Err


@final
class Rule(ValueObject):
    """Single rule with a mandatory name and optional description."""

    __slots__ = ("_name", "_content", "_description")

    _name: str
    _description: str | None
    _content: str

    @staticmethod
    def try_create(
        name: str, _content: str, description: str | None = None
    ) -> Result["Rule", str]:
        trimmed_name = name.strip()
        if not trimmed_name:
            return Err("Rule name cannot be empty.")
        desc = description.strip() if description else None
        return Ok(Rule(trimmed_name, _content, desc))

    def __init__(self, name: str, content: str, description: str | None) -> None:
        self._name = name
        self._description = description
        self._content = content

    def name(self) -> str:
        return self._name

    def description(self) -> str | None:
        return self._description

    def content(self) -> str:
        return self._content


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
