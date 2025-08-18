from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_path_recent_repository_loaded_list import (
    AddPathToRecentRepositoryListUseCase,
)
from codebase_to_llm.domain.user import User

from .dependencies import get_current_user, get_user_repositories
from .schemas import AddRecentRepositoryPathRequest

router = APIRouter(prefix="/recent-repositories", tags=["Recent Repositories"])


@router.post("/", summary="Add recent repository path")
def add_recent_repository_path(
    request: AddRecentRepositoryPathRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Add a repository path to the recent repositories list."""
    _, _, _, recent_repo, _ = get_user_repositories(current_user)
    use_case = AddPathToRecentRepositoryListUseCase()
    result = use_case.execute(Path(request.path), recent_repo)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"path": request.path}
