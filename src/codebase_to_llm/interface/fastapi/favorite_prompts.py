from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_favorite_prompt import AddFavoritePromptUseCase
from codebase_to_llm.application.uc_update_favorite_prompt import (
    UpdateFavoritePromptUseCase,
)
from codebase_to_llm.application.uc_remove_favorite_prompt import (
    RemoveFavoritePromptUseCase,
)
from codebase_to_llm.application.uc_get_favorite_prompts import (
    GetFavoritePromptsUseCase,
)
from codebase_to_llm.application.uc_get_favorite_prompt import GetFavoritePromptUseCase
from codebase_to_llm.domain.user import User

from .dependencies import get_current_user, get_user_repositories
from .schemas import (
    FavoritePromptCreateRequest,
    FavoritePromptUpdateRequest,
    FavoritePromptIdRequest,
)

router = APIRouter(
    prefix="/favorite-prompts",
    tags=["Favorite Prompts"],
)


@router.get("/", summary="Get all favorite prompts")
def get_favorite_prompts(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[dict[str, str]]]:
    """Get all favorite prompts for the authenticated user."""
    _, _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
    use_case = GetFavoritePromptsUseCase(favorite_prompts_repo)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompts = result.ok()
    assert prompts is not None
    return {
        "prompts": [
            {
                "id": p.id().value(),
                "name": p.name(),
                "content": p.content(),
            }
            for p in prompts.prompts()
        ]
    }


@router.get("/{prompt_id}", summary="Get favorite prompt by ID")
def get_favorite_prompt(
    prompt_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Get a specific favorite prompt by ID."""
    _, _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
    use_case = GetFavoritePromptUseCase(favorite_prompts_repo)
    result = use_case.execute(prompt_id)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {
        "id": prompt.id().value(),
        "name": prompt.name(),
        "content": prompt.content(),
    }


@router.post("/", summary="Create a new favorite prompt")
def add_favorite_prompt(
    request: FavoritePromptCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Create a new favorite prompt."""
    _, _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
    use_case = AddFavoritePromptUseCase(favorite_prompts_repo)
    result = use_case.execute(request.name, request.content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {
        "id": prompt.id().value(),
        "name": prompt.name(),
        "content": prompt.content(),
    }


@router.put("/", summary="Update a favorite prompt")
def update_favorite_prompt(
    request: FavoritePromptUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update an existing favorite prompt."""
    _, _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
    use_case = UpdateFavoritePromptUseCase(favorite_prompts_repo)
    result = use_case.execute(request.id, request.name, request.content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {
        "id": prompt.id().value(),
        "name": prompt.name(),
        "content": prompt.content(),
    }


@router.delete("/", summary="Delete a favorite prompt")
def remove_favorite_prompt(
    request: FavoritePromptIdRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete a favorite prompt."""
    _, _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
    use_case = RemoveFavoritePromptUseCase(favorite_prompts_repo)
    result = use_case.execute(request.id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"id": request.id}
