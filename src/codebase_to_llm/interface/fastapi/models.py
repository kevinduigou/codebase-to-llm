from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_model import AddModelUseCase
from codebase_to_llm.application.uc_load_models import LoadModelsUseCase
from codebase_to_llm.application.uc_update_model import UpdateModelUseCase
from codebase_to_llm.application.uc_remove_model import RemoveModelUseCase
from codebase_to_llm.domain.user import User

from .dependencies import get_current_user, get_user_repositories
from .schemas import AddModelRequest, UpdateModelRequest

router = APIRouter(prefix="/models", tags=["Models"])


@router.post("/", summary="Add a new model")
def add_model(
    request: AddModelRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Add a new LLM model configuration."""
    api_key_repo, model_repo, _, _, _ = get_user_repositories(current_user)
    use_case = AddModelUseCase(model_repo, api_key_repo)
    result = use_case.execute(
        current_user.id().value(),
        request.id_value,
        request.name,
        request.api_key_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    model = event.model()
    return {
        "id": model.id().value(),
        "name": model.name().value(),
        "api_key_id": model.api_key_id().value(),
    }


@router.get("/", summary="List all models")
def load_models(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, str]]:
    """Get all LLM models for the authenticated user."""
    _, model_repo, _, _, _ = get_user_repositories(current_user)
    use_case = LoadModelsUseCase(model_repo)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    models = result.ok()
    if models is None:
        return []
    return [
        {
            "id": m.id().value(),
            "name": m.name().value(),
            "api_key_id": m.api_key_id().value(),
        }
        for m in models.models()
    ]


@router.put("/", summary="Update a model")
def update_model(
    request: UpdateModelRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update an existing model configuration."""
    api_key_repo, model_repo, _, _, _ = get_user_repositories(current_user)
    use_case = UpdateModelUseCase(model_repo, api_key_repo)
    result = use_case.execute(
        current_user.id().value(),
        request.model_id,
        request.new_name,
        request.new_api_key_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    model = event.model()
    return {
        "id": model.id().value(),
        "name": model.name().value(),
        "api_key_id": model.api_key_id().value(),
    }


@router.delete("/{model_id}", summary="Delete a model")
def remove_model(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete a model configuration by ID."""
    _, model_repo, _, _, _ = get_user_repositories(current_user)
    use_case = RemoveModelUseCase(model_repo)
    result = use_case.execute(model_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"id": model_id}
