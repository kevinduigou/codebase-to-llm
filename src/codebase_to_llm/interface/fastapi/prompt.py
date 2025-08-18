from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_prompt_from_file import (
    AddPromptFromFileUseCase,
)
from codebase_to_llm.application.uc_modify_prompt import ModifyPromptUseCase
from codebase_to_llm.application.uc_set_prompt_from_favorite import (
    AddPromptFromFavoriteLisUseCase,
)
from codebase_to_llm.application.uc_add_file_as_prompt_variable import (
    AddFileAsPromptVariableUseCase,
)
from codebase_to_llm.domain.user import User

from .dependencies import _directory_repo, _prompt_repo, get_current_user
from .schemas import (
    AddFileAsPromptVariableRequest,
    AddPromptFromFileRequest,
    ModifyPromptRequest,
    SetPromptFromFavoriteRequest,
)

router = APIRouter(prefix="/prompt", tags=["Prompt Management"])


@router.post("/from-file", summary="Load prompt from file")
def add_prompt_from_file(
    request: AddPromptFromFileRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Load a prompt from a file."""
    use_case = AddPromptFromFileUseCase(_prompt_repo)
    result = use_case.execute(Path(request.path))
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {"content": prompt.get_content()}


@router.post("/modify", summary="Modify current prompt")
def modify_prompt(
    request: ModifyPromptRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Modify the current prompt content."""
    use_case = ModifyPromptUseCase(_prompt_repo)
    result = use_case.execute(request.new_content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    return {"content": event.new_prompt.get_content()}


@router.post("/from-favorite", summary="Set prompt from favorite")
def set_prompt_from_favorite(
    request: SetPromptFromFavoriteRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Set the current prompt from a favorite prompt."""
    use_case = AddPromptFromFavoriteLisUseCase(_prompt_repo)
    result = use_case.execute(request.content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {"content": prompt.get_content()}


@router.post("/variable", summary="Add file as prompt variable")
def add_file_as_prompt_variable(
    request: AddFileAsPromptVariableRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Add a file as a variable in the prompt."""
    use_case = AddFileAsPromptVariableUseCase(_prompt_repo)
    result = use_case.execute(
        _directory_repo, request.variable_key, Path(request.relative_path)
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    return {"file_path": event.file_path, "variable_key": event.variable_key}
