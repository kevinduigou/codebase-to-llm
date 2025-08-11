from __future__ import annotations

from pathlib import Path

from codebase_to_llm.application.uc_add_rule import AddRuleUseCase
from codebase_to_llm.application.uc_get_rules import GetRulesUseCase
from codebase_to_llm.application.uc_update_rule import UpdateRuleUseCase
from codebase_to_llm.application.uc_remove_rule import RemoveRuleUseCase
from codebase_to_llm.infrastructure.filesystem_rules_repository import (
    RulesRepository,
)


def _repo(tmp_path: Path) -> RulesRepository:
    return RulesRepository(tmp_path / "rules.json")


def test_add_and_get_rules(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    add_uc = AddRuleUseCase(repo)
    result = add_uc.execute("rule1", "content1", "desc1", True)
    assert result.is_ok()

    get_uc = GetRulesUseCase(repo)
    rules_result = get_uc.execute()
    assert rules_result.is_ok()
    rules = rules_result.ok()
    assert rules is not None
    assert len(rules.rules()) == 1
    rule = rules.rules()[0]
    assert rule.name() == "rule1"
    assert rule.content() == "content1"
    assert rule.description() == "desc1"
    assert rule.enabled()


def test_update_and_remove_rule(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    add_uc = AddRuleUseCase(repo)
    add_result = add_uc.execute("rule1", "content1", None, True)
    assert add_result.is_ok()

    update_uc = UpdateRuleUseCase(repo)
    update_result = update_uc.execute("rule1", "new", "d", False)
    assert update_result.is_ok()

    get_uc = GetRulesUseCase(repo)
    rules_result = get_uc.execute()
    assert rules_result.is_ok()
    rules = rules_result.ok()
    assert rules is not None
    rule = rules.rules()[0]
    assert rule.content() == "new"
    assert rule.description() == "d"
    assert not rule.enabled()

    remove_uc = RemoveRuleUseCase(repo)
    remove_result = remove_uc.execute("rule1")
    assert remove_result.is_ok()

    rules_after = get_uc.execute().ok()
    assert rules_after is not None
    assert len(rules_after.rules()) == 0
