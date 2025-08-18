from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_api_key import AddApiKeyUseCase
from codebase_to_llm.application.uc_load_api_keys import LoadApiKeysUseCase
from codebase_to_llm.application.uc_update_api_key import UpdateApiKeyUseCase
from codebase_to_llm.application.uc_remove_api_key import RemoveApiKeyUseCase
from codebase_to_llm.domain.user import User

from .dependencies import get_current_user, get_user_repositories
from .schemas import AddApiKeyRequest, UpdateApiKeyRequest

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("/", summary="Add a new API key")
def add_api_key(
    request: AddApiKeyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Add a new API key for the authenticated user."""
    api_key_repo, _, _, _, _ = get_user_repositories(current_user)
    use_case = AddApiKeyUseCase(api_key_repo)
    result = use_case.execute(
        current_user.id().value(),
        request.id_value,
        request.url_provider,
        request.api_key_value,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    api_key = event.api_key()
    return {
        "id": api_key.id().value(),
        "url_provider": api_key.url_provider().value(),
        "api_key_value": api_key.api_key_value().value(),
    }


@router.get("/", summary="List all API keys")
def load_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, str]]:
    """Get all API keys for the authenticated user."""
    api_key_repo, _, _, _, _ = get_user_repositories(current_user)
    use_case = LoadApiKeysUseCase(api_key_repo)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    keys = result.ok()
    if keys is None:
        return []
    return [
        {
            "id": key.id().value(),
            "url_provider": key.url_provider().value(),
            "api_key_value": key.api_key_value().value(),
        }
        for key in keys.api_keys()
    ]


@router.put("/", summary="Update an API key")
def update_api_key(
    request: UpdateApiKeyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update an existing API key."""
    api_key_repo, _, _, _, _ = get_user_repositories(current_user)
    use_case = UpdateApiKeyUseCase(api_key_repo)
    result = use_case.execute(
        request.api_key_id, request.new_url_provider, request.new_api_key_value
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    api_key = event.api_key()
    return {
        "id": api_key.id().value(),
        "url_provider": api_key.url_provider().value(),
        "api_key_value": api_key.api_key_value().value(),
    }


@router.delete("/{api_key_id}", summary="Delete an API key")
def remove_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete an API key by ID."""
    api_key_repo, _, _, _, _ = get_user_repositories(current_user)
    use_case = RemoveApiKeyUseCase(api_key_repo)
    result = use_case.execute(api_key_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"id": api_key_id}
