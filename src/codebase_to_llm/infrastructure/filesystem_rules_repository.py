from __future__ import annotations

from pathlib import Path
from typing import Final

import json

from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.application.ports import RulesRepositoryPort
from codebase_to_llm.domain.rules import Rule, Rules


class FileSystemRulesRepository(RulesRepositoryPort):
    """Reads / writes the rules text in the user’s home directory."""

    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None):
        default_path = Path.home() / ".copy_to_llm" / "rules"
        self._path: Final = path or default_path

    # -------------------------------------------------------------- public API
    def load_rules(self) -> Result[Rules, str]:
        try:  # I/O happens in infra, so a *try* is acceptable here
            if not self._path.exists():
                return Err("Rules file not found.")
            raw = self._path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(raw) if raw.strip() else []
            rules: list[Rule] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        name = str(item.get("name", ""))
                        description_raw = item.get("description")
                        content_raw = item.get("content")
                        description = (
                            str(description_raw)
                            if description_raw is not None
                            else None
                        )
                        rule_result = Rule.try_create(name, content_raw, description)
                        if rule_result.is_err():
                            return Err(rule_result.err())
                        rule = rule_result.ok()
                        assert rule is not None
                        rules.append(rule)
            rules_result = Rules.try_create(rules)
            if rules_result.is_err():
                return Err(rules_result.err())
            return Ok(rules_result.ok())
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def save_rules(self, rules: Rules) -> Result[None, str]:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = [
                {
                    "name": rule.name(),
                    "content": rule.content(),
                    "description": rule.description(),
                }
                for rule in rules.rules()
            ]
            self._path.write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
