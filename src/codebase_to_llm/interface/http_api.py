from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, final

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from codebase_to_llm.application.uc_add_api_key import AddApiKeyUseCase
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
from codebase_to_llm.application.uc_add_favorite_prompt import (
    AddFavoritePromptUseCase,
)
from codebase_to_llm.application.uc_update_favorite_prompt import (
    UpdateFavoritePromptUseCase,
)
from codebase_to_llm.application.uc_remove_favorite_prompt import (
    RemoveFavoritePromptUseCase,
)
from codebase_to_llm.application.uc_get_favorite_prompts import (
    GetFavoritePromptsUseCase,
)
from codebase_to_llm.application.uc_get_favorite_prompt import (
    GetFavoritePromptUseCase,
)
from codebase_to_llm.application.uc_add_rule import AddRuleUseCase
from codebase_to_llm.application.uc_get_rules import GetRulesUseCase
from codebase_to_llm.application.uc_update_rule import UpdateRuleUseCase
from codebase_to_llm.application.uc_remove_rule import RemoveRuleUseCase
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.application.uc_get_file import GetFileUseCase
from codebase_to_llm.application.uc_update_file import UpdateFileUseCase
from codebase_to_llm.application.uc_delete_file import DeleteFileUseCase
from codebase_to_llm.application.uc_add_directory import AddDirectoryUseCase
from codebase_to_llm.application.uc_get_directory import GetDirectoryUseCase
from codebase_to_llm.application.uc_update_directory import UpdateDirectoryUseCase
from codebase_to_llm.application.uc_delete_directory import DeleteDirectoryUseCase
from codebase_to_llm.domain.api_key import ApiKeyId
from codebase_to_llm.application.uc_register_user import RegisterUserUseCase
from codebase_to_llm.application.uc_authenticate_user import AuthenticateUserUseCase
from codebase_to_llm.application.uc_validate_user import ValidateUserUseCase
from codebase_to_llm.domain.user import User, UserName

from codebase_to_llm.infrastructure.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_recent_repository import (
    SqlAlchemyRecentRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_rules_repository import (
    SqlAlchemyRulesRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_favorite_prompts_repository import (
    SqlAlchemyFavoritePromptsRepository,
)
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
from codebase_to_llm.infrastructure.brevo_email_sender import BrevoEmailSender
from codebase_to_llm.infrastructure.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_directory_repository import (
    SqlAlchemyDirectoryRepository,
)
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage

# Load environment variables from .env-development file
load_dotenv(".env-development")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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

# Add CORS middleware
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/")
def serve_web_ui() -> FileResponse:
    """Serve the web UI HTML file."""
    html_file_path = Path(__file__).parent / "web_ui.html"
    return FileResponse(html_file_path, media_type="text/html")


@app.get("/login")
def serve_login_ui() -> FileResponse:
    """Serve the login UI HTML file."""
    html_file_path = Path(__file__).parent / "login.html"
    return FileResponse(html_file_path, media_type="text/html")


@app.get("/register")
def serve_register_ui() -> FileResponse:
    """Serve the registration UI HTML file."""
    html_file_path = Path(__file__).parent / "register.html"
    return FileResponse(html_file_path, media_type="text/html")


@app.get("/favorite-prompts-ui")
def serve_favorite_prompts_ui() -> FileResponse:
    """Serve the favorite prompts management UI."""
    html_file_path = Path(__file__).parent / "favorite_prompts.html"
    return FileResponse(html_file_path, media_type="text/html")


@app.get("/file-manager-test")
def serve_file_manager_test_ui() -> FileResponse:
    """Serve the file and directory manager test interface."""
    html_file_path = Path(__file__).parent / "file_manager_test.html"
    return FileResponse(html_file_path, media_type="text/html")


@app.get("/web_ui.css")
def serve_css() -> FileResponse:
    """Serve the CSS file."""
    css_file_path = Path(__file__).parent / "web_ui.css"
    return FileResponse(css_file_path, media_type="text/css")


# Repositories and services shared across requests (user-independent)
_context_buffer = InMemoryContextBufferRepository()
_prompt_repo = InMemoryPromptRepository()
_external_repo = UrlExternalSourceRepository()
_clipboard = InMemoryClipboardService()
_directory_repo = FileSystemDirectoryRepository(Path.cwd())
_llm_adapter = OpenAILLMAdapter()
_user_repo = SqlAlchemyUserRepository()
_email_sender = BrevoEmailSender()
_file_repo = SqlAlchemyFileRepository()
_directory_structure_repo = SqlAlchemyDirectoryRepository()
_file_storage = GCPFileStorage()


def get_user_repositories(user: User) -> tuple[
    SqlAlchemyApiKeyRepository,
    SqlAlchemyRulesRepository,
    SqlAlchemyRecentRepository,
    SqlAlchemyFavoritePromptsRepository,
]:
    """Create user-specific repository instances."""
    user_id = user.id().value()
    return (
        SqlAlchemyApiKeyRepository(user_id),
        SqlAlchemyRulesRepository(user_id),
        SqlAlchemyRecentRepository(user_id),
        SqlAlchemyFavoritePromptsRepository(user_id),
    )


class RegisterRequest(BaseModel):
    user_name: str
    email: str
    password: str


@app.post("/register")
def register_user(request: RegisterRequest) -> dict[str, str]:
    use_case = RegisterUserUseCase(_user_repo, _email_sender)
    result = use_case.execute(request.user_name, request.email, request.password)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    user = result.ok()
    assert user is not None
    return {"id": user.id().value(), "user_name": user.name().value()}


@app.get("/validate")
def validate_user(token: str) -> FileResponse:
    """Validate user account using the token from email."""
    use_case = ValidateUserUseCase(_user_repo)
    result = use_case.execute(token)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())

    # Redirect to login page after successful validation
    html_file_path = Path(__file__).parent / "validation_success.html"
    return FileResponse(html_file_path, media_type="text/html")


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    name_result = UserName.try_create(str(username))
    if name_result.is_err():
        raise credentials_exception
    name = name_result.ok()
    if name is None:
        raise credentials_exception

    repo_result = _user_repo.find_by_name(name)
    if repo_result.is_err():
        raise credentials_exception
    user = repo_result.ok()
    if user is None:
        raise credentials_exception
    return user


@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    use_case = AuthenticateUserUseCase(_user_repo)
    result = use_case.execute(form_data.username, form_data.password)
    if result.is_err():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.err(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = result.ok()
    assert user is not None
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.name().value()}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


class AddApiKeyRequest(BaseModel):
    id_value: str
    url_provider: str
    api_key_value: str


@app.post("/api-keys")
def add_api_key(
    request: AddApiKeyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    api_key_repo, _, _, _ = get_user_repositories(current_user)
    use_case = AddApiKeyUseCase(api_key_repo)
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
def load_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, str]]:
    api_key_repo, _, _, _ = get_user_repositories(current_user)
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


class UpdateApiKeyRequest(BaseModel):
    api_key_id: str
    new_url_provider: str
    new_api_key_value: str


@app.put("/api-keys")
def update_api_key(
    request: UpdateApiKeyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    api_key_repo, _, _, _ = get_user_repositories(current_user)
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


@app.delete("/api-keys/{api_key_id}")
def remove_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    api_key_repo, _, _, _ = get_user_repositories(current_user)
    use_case = RemoveApiKeyUseCase(api_key_repo)
    result = use_case.execute(api_key_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"id": api_key_id}


class AddFileRequest(BaseModel):
    path: str


@app.post("/context-buffer/file")
def add_file_to_context_buffer(
    request: AddFileRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
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
def add_snippet_to_context_buffer(
    request: AddSnippetRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
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
    include_timestamps: bool = False


@app.post("/context-buffer/external")
def add_external_source(
    request: AddExternalSourceRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    use_case = AddExternalSourceToContextBufferUseCase(_context_buffer, _external_repo)
    result = use_case.execute(request.url, request.include_timestamps)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    url_val = result.ok()
    assert url_val is not None
    return {"url": url_val}


@app.get("/context-buffer/external")
def get_external_sources(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    use_case = GetExternalSourcesUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    sources = result.ok() or []
    return {"external_sources": [src.url for src in sources]}


class RemoveExternalSourceRequest(BaseModel):
    url: str


@app.delete("/context-buffer/external")
def remove_external_source(
    request: RemoveExternalSourceRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    use_case = RemoveExternalSourceUseCase(_context_buffer)
    result = use_case.execute(request.url)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"removed": request.url}


@app.delete("/context-buffer/external/all")
def remove_all_external_sources(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    use_case = RemoveAllExternalSourcesUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "cleared"}


@app.delete("/context-buffer/all")
def clear_context_buffer(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    use_case = ClearContextBufferUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "cleared"}


class RemoveElementsRequest(BaseModel):
    elements: list[str]


@app.delete("/context-buffer")
def remove_elements_from_context_buffer(
    request: RemoveElementsRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    use_case = RemoveElementsFromContextBufferUseCase(_context_buffer)
    result = use_case.execute(request.elements)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"removed": request.elements}


class AddPromptFromFileRequest(BaseModel):
    path: str


@app.post("/prompt/from-file")
def add_prompt_from_file(
    request: AddPromptFromFileRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
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
def modify_prompt(
    request: ModifyPromptRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
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
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    use_case = AddPromptFromFavoriteLisUseCase(_prompt_repo)
    result = use_case.execute(request.content)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    prompt = result.ok()
    assert prompt is not None
    return {"content": prompt.get_content()}


class FavoritePromptCreateRequest(BaseModel):
    name: str
    content: str


class FavoritePromptUpdateRequest(BaseModel):
    id: str
    name: str
    content: str


class FavoritePromptIdRequest(BaseModel):
    id: str


@app.get("/favorite-prompts")
def get_favorite_prompts(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[dict[str, str]]]:
    _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
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


@app.get("/favorite-prompt/{prompt_id}")
def get_favorite_prompt(
    prompt_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
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


@app.post("/favorite-prompts")
def add_favorite_prompt(
    request: FavoritePromptCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
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


@app.put("/favorite-prompts")
def update_favorite_prompt(
    request: FavoritePromptUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
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


@app.delete("/favorite-prompts")
def remove_favorite_prompt(
    request: FavoritePromptIdRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _, _, _, favorite_prompts_repo = get_user_repositories(current_user)
    use_case = RemoveFavoritePromptUseCase(favorite_prompts_repo)
    result = use_case.execute(request.id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"id": request.id}


class RuleCreateRequest(BaseModel):
    name: str
    content: str
    description: str | None = None
    enabled: bool = True


class RuleUpdateRequest(BaseModel):
    name: str
    content: str
    description: str | None = None
    enabled: bool = True


class RuleNameRequest(BaseModel):
    name: str


@app.get("/rules")
def get_rules(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    _, rules_repo, _, _ = get_user_repositories(current_user)
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


@app.post("/rules")
def add_rule(
    request: RuleCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    _, rules_repo, _, _ = get_user_repositories(current_user)
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


@app.put("/rules")
def update_rule(
    request: RuleUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    _, rules_repo, _, _ = get_user_repositories(current_user)
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


@app.delete("/rules")
def remove_rule(
    request: RuleNameRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = RemoveRuleUseCase(rules_repo)
    result = use_case.execute(request.name)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"name": request.name}


class AddFileAsPromptVariableRequest(BaseModel):
    variable_key: str
    relative_path: str


@app.post("/prompt/variable")
def add_file_as_prompt_variable(
    request: AddFileAsPromptVariableRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _, _, recent_repo, _ = get_user_repositories(current_user)
    use_case = AddPathToRecentRepositoryListUseCase()
    result = use_case.execute(Path(request.path), recent_repo)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"path": request.path}


class GenerateResponseRequest(BaseModel):
    model: str
    api_key_id: str
    include_tree: bool = True
    root_directory_path: str | None = None


@app.post("/llm-response")
def generate_llm_response(
    request: GenerateResponseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    api_key_repo, rules_repo, _, _ = get_user_repositories(current_user)
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
        api_key_repo,
        _directory_repo,
        _prompt_repo,
        _context_buffer,
        rules_repo,
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
def copy_context(
    request: CopyContextRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _, rules_repo, _, _ = get_user_repositories(current_user)
    use_case = CopyContextUseCase(_context_buffer, rules_repo, _clipboard)
    result = use_case.execute(
        _directory_repo, _prompt_repo, request.include_tree, request.root_directory_path
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"content": _clipboard.text()}


class UploadFileRequest(BaseModel):
    name: str
    content: str
    directory_id: str | None = None


@app.post("/files")
def upload_file(
    request: UploadFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    file_id = str(uuid.uuid4())
    use_case = AddFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(
        file_id,
        current_user.id().value(),
        request.name,
        request.content.encode("utf-8"),
        request.directory_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    file = result.ok()
    assert file is not None
    return {"id": file.id().value(), "name": file.name()}


@app.get("/files/{file_id}")
def get_file(
    file_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str | None]:
    use_case = GetFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(current_user.id().value(), file_id)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    file, content = result.ok() or (None, b"")
    assert file is not None
    dir_id = file.directory_id()
    return {
        "id": file.id().value(),
        "name": file.name(),
        "directory_id": dir_id.value() if dir_id is not None else None,
        "content": content.decode("utf-8"),
    }


class UpdateFileRequest(BaseModel):
    new_name: str | None = None
    new_directory_id: str | None = None


@app.put("/files/{file_id}")
def update_file(
    file_id: str,
    request: UpdateFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    use_case = UpdateFileUseCase(_file_repo)
    result = use_case.execute(
        current_user.id().value(),
        file_id,
        request.new_name,
        request.new_directory_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "updated"}


@app.delete("/files/{file_id}")
def delete_file(
    file_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    use_case = DeleteFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(current_user.id().value(), file_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}


class CreateDirectoryRequest(BaseModel):
    id_value: str
    name: str
    parent_id: str | None = None


@app.post("/directories")
def create_directory(
    request: CreateDirectoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str | None]:
    use_case = AddDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(
        request.id_value,
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


@app.get("/directories/{directory_id}")
def get_directory(
    directory_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str | None]:
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


class UpdateDirectoryRequest(BaseModel):
    new_name: str | None = None
    new_parent_id: str | None = None


@app.put("/directories/{directory_id}")
def update_directory(
    directory_id: str,
    request: UpdateDirectoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
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


@app.delete("/directories/{directory_id}")
def delete_directory(
    directory_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    use_case = DeleteDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(current_user.id().value(), directory_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}
