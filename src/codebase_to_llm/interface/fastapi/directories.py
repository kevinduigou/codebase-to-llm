from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_directory import AddDirectoryUseCase
from codebase_to_llm.application.uc_get_directory import GetDirectoryUseCase
from codebase_to_llm.application.uc_update_directory import UpdateDirectoryUseCase
from codebase_to_llm.application.uc_delete_directory import DeleteDirectoryUseCase
from codebase_to_llm.domain.user import User

from .dependencies import _directory_structure_repo, get_current_user
from .schemas import CreateDirectoryRequest, UpdateDirectoryRequest

router = APIRouter(prefix="/directories", tags=["Directory Management"])


@router.post("/", summary="Create a new directory")
def create_directory(
    request: CreateDirectoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str | None]:
    """Create a new directory."""
    directory_id = str(uuid.uuid4())
    use_case = AddDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(
        directory_id,
        current_user.id().value(),
        request.name,
        request.parent_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    directory = result.ok()
    assert directory is not None
    parent = directory.parent_id()
    return {
        "id": directory.id().value(),
        "name": directory.name(),
        "parent_id": parent.value() if parent is not None else None,
    }


@router.get("/{directory_id}", summary="Get directory by ID")
def get_directory(
    directory_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str | None]:
    """Get a directory by its ID."""
    use_case = GetDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(current_user.id().value(), directory_id)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    directory = result.ok()
    assert directory is not None
    parent = directory.parent_id()
    return {
        "id": directory.id().value(),
        "name": directory.name(),
        "parent_id": parent.value() if parent is not None else None,
    }


@router.put("/{directory_id}", summary="Update directory")
def update_directory(
    directory_id: str,
    request: UpdateDirectoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update directory metadata."""
    use_case = UpdateDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(
        current_user.id().value(),
        directory_id,
        request.new_name,
        request.new_parent_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "updated"}


@router.delete("/{directory_id}", summary="Delete directory")
def delete_directory(
    directory_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete a directory by its ID."""
    use_case = DeleteDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(current_user.id().value(), directory_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}
