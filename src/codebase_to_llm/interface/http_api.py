from __future__ import annotations

from pathlib import Path
from typing import Any, final

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from codebase_to_llm.application.uc_add_api_key import AddApiKeyUseCase
from codebase_to_llm.application.uc_add_code_snippet_to_context_buffer import (
    AddCodeSnippetToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_external_source import (
    AddExternalSourceToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_file_as_prompt_variable import (
    AddFileAsPromptVariableUseCase,
)
from codebase_to_llm.application.uc_add_file_to_context_buffer import (
    AddFileToContextBufferUseCase,
)
from codebase_to_llm.application.uc_add_path_recent_repository_loaded_list import (
    AddPathToRecentRepositoryListUseCase,
)
from codebase_to_llm.application.uc_add_prompt_from_file import (
    AddPromptFromFileUseCase,
)
from codebase_to_llm.application.uc_copy_context import CopyContextUseCase
from codebase_to_llm.application.uc_generate_llm_response import (
    GenerateLLMResponseUseCase,
)
from codebase_to_llm.application.uc_load_api_keys import LoadApiKeysUseCase
from codebase_to_llm.application.uc_modify_prompt import ModifyPromptUseCase
from codebase_to_llm.application.uc_remove_api_key import RemoveApiKeyUseCase
from codebase_to_llm.application.uc_remove_elmts_from_context_buffer import (
    RemoveElementsFromContextBufferUseCase,
)
from codebase_to_llm.application.uc_set_prompt_from_favorite import (
    AddPromptFromFavoriteLisUseCase,
)
from codebase_to_llm.application.uc_update_api_key import UpdateApiKeyUseCase
from codebase_to_llm.domain.api_key import ApiKeyId
from codebase_to_llm.application.uc_register_user import RegisterUserUseCase
from codebase_to_llm.application.uc_authenticate_user import AuthenticateUserUseCase

from codebase_to_llm.infrastructure.filesystem_api_key_repository import (
    FileSystemApiKeyRepository,
)
from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)
from codebase_to_llm.infrastructure.filesystem_recent_repository import (
    FileSystemRecentRepository,
)
from codebase_to_llm.infrastructure.filesystem_rules_repository import RulesRepository
from codebase_to_llm.infrastructure.in_memory_context_buffer_repository import (
    InMemoryContextBufferRepository,
)
from codebase_to_llm.infrastructure.in_memory_prompt_repository import (
    InMemoryPromptRepository,
)
from codebase_to_llm.infrastructure.llm_adapter import OpenAILLMAdapter
from codebase_to_llm.infrastructure.url_external_source_repository import (
    UrlExternalSourceRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


@final
class InMemoryClipboardService:
    """Simple clipboard service used for the HTTP interface."""

    __slots__ = ("_content",)
    _content: str

    def __init__(self) -> None:
        self._content = ""

    def set_text(self, text: str) -> None:
        self._content = text

    def text(self) -> str:
        return self._content


app = FastAPI()

# Repositories and services shared across requests
_api_key_repo = FileSystemApiKeyRepository()
_context_buffer = InMemoryContextBufferRepository()
_prompt_repo = InMemoryPromptRepository()
_rules_repo = RulesRepository()
_external_repo = UrlExternalSourceRepository()
_recent_repo = FileSystemRecentRepository()
_clipboard = InMemoryClipboardService()
_directory_repo = FileSystemDirectoryRepository(Path.cwd())
_llm_adapter = OpenAILLMAdapter()
_user_repo = SqlAlchemyUserRepository()


class RegisterRequest(BaseModel):
    user_name: str
    password: str


@app.post("/register")
def register_user(request: RegisterRequest) -> dict[str, str]:
    use_case = RegisterUserUseCase(_user_repo)
    result = use_case.execute(request.user_name, request.password)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    user = result.ok()
    assert user is not None
    return {"id": user.id().value(), "user_name": user.name().value()}


class LoginRequest(BaseModel):
    user_name: str
    password: str


@app.post("/login")
def login_user(request: LoginRequest) -> dict[str, str]:
    use_case = AuthenticateUserUseCase(_user_repo)
    result = use_case.execute(request.user_name, request.password)
    if result.is_err():
        raise HTTPException(status_code=401, detail=result.err())
    user = result.ok()
    assert user is not None
    return {"id": user.id().value(), "user_name": user.name().value()}


class AddApiKeyRequest(BaseModel):
    id_value: str
    url_provider: str
    api_key_value: str


@app.post("/api-keys")
def add_api_key(request: AddApiKeyRequest) -> dict[str, str]:
    use_case = AddApiKeyUseCase(_api_key_repo)
    result = use_case.execute(
        request.id_value, request.url_provider, request.api_key_value
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


@app.get("/api-keys")
def load_api_keys() -> list[dict[str, str]]:
    use_case = LoadApiKeysUseCase(_api_key_repo)
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


class UpdateApiKeyRequest(BaseModel):
    api_key_id: str
    new_url_provider: str
    new_api_key_value: str


@app.put("/api-keys")
def update_api_key(request: UpdateApiKeyRequest) -> dict[str, str]:
    use_case = UpdateApiKeyUseCase(_api_key_repo)
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


@app.delete("/api-keys/{api_key_id}")
def remove_api_key(api_key_id: str) -> dict[str, str]:
    use_case = RemoveApiKeyUseCase(_api_key_repo)
    result = use_case.execute(api_key_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"id": api_key_id}


class AddFileRequest(BaseModel):
    path: str


@app.post("/context-buffer/file")
def add_file_to_context_buffer(request: AddFileRequest) -> dict[str, str]:
    use_case = AddFileToContextBufferUseCase(_context_buffer)
    result = use_case.execute(Path(request.path))
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"path": request.path}


class AddSnippetRequest(BaseModel):
    path: str
    start: int
    end: int
    text: str


@app.post("/context-buffer/snippet")
def add_snippet_to_context_buffer(request: AddSnippetRequest) -> dict[str, Any]:
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


class AddExternalSourceRequest(BaseModel):
    url: str


@app.post("/context-buffer/external")
def add_external_source(request: AddExternalSourceRequest) -> dict[str, str]:
    use_case = AddExternalSourceToContextBufferUseCase(_context_buffer, _external_repo)
    result = use_case.execute(request.url)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    url_val = result.ok()
    assert url_val is not None
    return {"url": url_val}


class RemoveElementsRequest(BaseModel):
    elements: list[str]


@app.delete("/context-buffer")
def remove_elements_from_context_buffer(
    request: RemoveElementsRequest,
) -> dict[str, list[str]]:
    use_case = RemoveElementsFromContextBufferUseCase(_context_buffer)
    result = use_case.execute(request.elements)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"removed": request.elements}


class AddPromptFromFileRequest(BaseModel):
    path: str


@app.post("/prompt/from-file")
def add_prompt_from_file(request: AddPromptFromFileRequest) -> dict[str, str]:
    use_case = AddPromptFromFileUseCase(_prompt_repo)
    result = use_case.execute(Path(request.path))
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {"content": prompt.get_content()}


class ModifyPromptRequest(BaseModel):
    new_content: str


@app.post("/prompt/modify")
def modify_prompt(request: ModifyPromptRequest) -> dict[str, str]:
    use_case = ModifyPromptUseCase(_prompt_repo)
    result = use_case.execute(request.new_content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    return {"content": event.new_prompt.get_content()}


class SetPromptFromFavoriteRequest(BaseModel):
    content: str


@app.post("/prompt/from-favorite")
def set_prompt_from_favorite(
    request: SetPromptFromFavoriteRequest,
) -> dict[str, str]:
    use_case = AddPromptFromFavoriteLisUseCase(_prompt_repo)
    result = use_case.execute(request.content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {"content": prompt.get_content()}


class AddFileAsPromptVariableRequest(BaseModel):
    variable_key: str
    relative_path: str


@app.post("/prompt/variable")
def add_file_as_prompt_variable(
    request: AddFileAsPromptVariableRequest,
) -> dict[str, str]:
    use_case = AddFileAsPromptVariableUseCase(_prompt_repo)
    result = use_case.execute(
        _directory_repo, request.variable_key, Path(request.relative_path)
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    return {"file_path": event.file_path, "variable_key": event.variable_key}


class AddRecentRepositoryPathRequest(BaseModel):
    path: str


@app.post("/recent-repositories")
def add_recent_repository_path(
    request: AddRecentRepositoryPathRequest,
) -> dict[str, str]:
    use_case = AddPathToRecentRepositoryListUseCase()
    result = use_case.execute(Path(request.path), _recent_repo)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"path": request.path}


class GenerateResponseRequest(BaseModel):
    model: str
    api_key_id: str
    include_tree: bool = True
    root_directory_path: str | None = None


@app.post("/llm-response")
def generate_llm_response(request: GenerateResponseRequest) -> dict[str, str]:
    api_key_id_result = ApiKeyId.try_create(request.api_key_id)
    if api_key_id_result.is_err():
        raise HTTPException(status_code=400, detail=api_key_id_result.err())
    api_key_id_obj = api_key_id_result.ok()
    assert api_key_id_obj is not None
    use_case = GenerateLLMResponseUseCase()
    result = use_case.execute(
        request.model,
        api_key_id_obj,
        _llm_adapter,
        _api_key_repo,
        _directory_repo,
        _prompt_repo,
        _context_buffer,
        _rules_repo,
        request.include_tree,
        request.root_directory_path,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    return {"response": event.response}


class CopyContextRequest(BaseModel):
    include_tree: bool = True
    root_directory_path: str | None = None


@app.post("/context/copy")
def copy_context(request: CopyContextRequest) -> dict[str, str]:
    use_case = CopyContextUseCase(_context_buffer, _rules_repo, _clipboard)
    result = use_case.execute(
        _directory_repo, _prompt_repo, request.include_tree, request.root_directory_path
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"content": _clipboard.text()}
