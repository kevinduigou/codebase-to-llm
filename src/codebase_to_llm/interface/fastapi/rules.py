from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_rule import AddRuleUseCase
from codebase_to_llm.application.uc_get_rules import GetRulesUseCase
from codebase_to_llm.application.uc_update_rule import UpdateRuleUseCase
from codebase_to_llm.application.uc_remove_rule import RemoveRuleUseCase
from codebase_to_llm.domain.user import User

from .dependencies import get_current_user, get_user_repositories
from .schemas import RuleCreateRequest, RuleUpdateRequest, RuleNameRequest

router = APIRouter(prefix="/rules", tags=["Rules Management"])


@router.get("/", summary="Get all rules")
def get_rules(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    """Get all rules for the authenticated user."""
    _, _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = GetRulesUseCase(rules_repo)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    rules = result.ok()
    assert rules is not None
    return [
        {
            "name": r.name(),
            "content": r.content(),
            "description": r.description(),
            "enabled": r.enabled(),
        }
        for r in rules.rules()
    ]


@router.post("/", summary="Create a new rule")
def add_rule(
    request: RuleCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a new rule."""
    _, _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = AddRuleUseCase(rules_repo)
    result = use_case.execute(
        request.name, request.content, request.description, request.enabled
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    rule = result.ok()
    assert rule is not None
    return {
        "name": rule.name(),
        "content": rule.content(),
        "description": rule.description(),
        "enabled": rule.enabled(),
    }


@router.put("/", summary="Update a rule")
def update_rule(
    request: RuleUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update an existing rule."""
    _, _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = UpdateRuleUseCase(rules_repo)
    result = use_case.execute(
        request.name, request.content, request.description, request.enabled
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    rule = result.ok()
    assert rule is not None
    return {
        "name": rule.name(),
        "content": rule.content(),
        "description": rule.description(),
        "enabled": rule.enabled(),
    }


@router.delete("/", summary="Delete a rule")
def remove_rule(
    request: RuleNameRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete a rule by name."""
    _, _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = RemoveRuleUseCase(rules_repo)
    result = use_case.execute(request.name)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"name": request.name}
