from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_add_file_to_context_buffer import (
    AddFileToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_code_snippet_to_context_buffer import (
    AddCodeSnippetToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_external_source import (
    AddExternalSourceToContextBufferUseCase,
)
from codebase_to_llm.application.uc_get_external_sources import (
    GetExternalSourcesUseCase,
)
from codebase_to_llm.application.uc_remove_external_source import (
    RemoveExternalSourceUseCase,
)
from codebase_to_llm.application.uc_remove_all_external_sources import (
    RemoveAllExternalSourcesUseCase,
)
from codebase_to_llm.application.uc_clear_context_buffer import (
    ClearContextBufferUseCase,
)
from codebase_to_llm.application.uc_remove_elmts_from_context_buffer import (
    RemoveElementsFromContextBufferUseCase,
)
from codebase_to_llm.application.uc_copy_context import CopyContextUseCase
from codebase_to_llm.domain.user import User

from .dependencies import (
    _clipboard,
    _context_buffer,
    _directory_repo,
    _external_repo,
    _prompt_repo,
    get_current_user,
    get_user_repositories,
)
from .schemas import (
    AddExternalSourceRequest,
    AddFileRequest,
    AddSnippetRequest,
    CopyContextRequest,
    RemoveElementsRequest,
    RemoveExternalSourceRequest,
)

router = APIRouter(prefix="/context-buffer", tags=["Context Buffer"])


@router.post("/file", summary="Add file to context buffer")
def add_file_to_context_buffer(
    request: AddFileRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Add a complete file to the context buffer."""
    use_case = AddFileToContextBufferUseCase(_context_buffer)
    result = use_case.execute(Path(request.path))
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"path": request.path}


@router.post("/snippet", summary="Add code snippet to context buffer")
def add_snippet_to_context_buffer(
    request: AddSnippetRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Add a specific code snippet to the context buffer."""
    use_case = AddCodeSnippetToContextBufferUseCase(_context_buffer)
    result = use_case.execute(
        Path(request.path), request.start, request.end, request.text
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    snippet = result.ok()
    assert snippet is not None
    return {
        "path": str(snippet.path),
        "start": snippet.start,
        "end": snippet.end,
    }


@router.post("/external", summary="Add external source to context buffer")
def add_external_source(
    request: AddExternalSourceRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Add an external URL source to the context buffer."""
    use_case = AddExternalSourceToContextBufferUseCase(_context_buffer, _external_repo)
    result = use_case.execute(request.url, request.include_timestamps)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    url_val = result.ok()
    assert url_val is not None
    return {"url": url_val}


@router.get("/external", summary="Get external sources")
def get_external_sources(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    """Get all external sources in the context buffer."""
    use_case = GetExternalSourcesUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    sources = result.ok() or []
    return {"external_sources": [src.url for src in sources]}


@router.delete("/external", summary="Remove external source")
def remove_external_source(
    request: RemoveExternalSourceRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Remove a specific external source from the context buffer."""
    use_case = RemoveExternalSourceUseCase(_context_buffer)
    result = use_case.execute(request.url)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"removed": request.url}


@router.delete("/external/all", summary="Remove all external sources")
def remove_all_external_sources(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Remove all external sources from the context buffer."""
    use_case = RemoveAllExternalSourcesUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "cleared"}


@router.delete("/all", summary="Clear entire context buffer")
def clear_context_buffer(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Clear all content from the context buffer."""
    use_case = ClearContextBufferUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "cleared"}


@router.delete("/", summary="Remove specific elements from context buffer")
def remove_elements_from_context_buffer(
    request: RemoveElementsRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    """Remove specific elements from the context buffer."""
    use_case = RemoveElementsFromContextBufferUseCase(_context_buffer)
    result = use_case.execute(request.elements)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"removed": request.elements}


@router.post("/copy", summary="Copy context to clipboard")
def copy_context(
    request: CopyContextRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Copy the current context to clipboard."""
    _, _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = CopyContextUseCase(_context_buffer, rules_repo, _clipboard)
    result = use_case.execute(
        _directory_repo, _prompt_repo, request.include_tree, request.root_directory_path
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"content": _clipboard.text()}
