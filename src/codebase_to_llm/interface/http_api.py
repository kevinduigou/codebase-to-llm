from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, final

import jwt
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from openai import Stream
from pydantic import BaseModel
from openai.types.responses import ResponseTextDeltaEvent, ResponseCompletedEvent

from codebase_to_llm.application.uc_add_api_key import AddApiKeyUseCase
from codebase_to_llm.application.uc_add_model import AddModelUseCase
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
from codebase_to_llm.application.uc_load_models import LoadModelsUseCase
from codebase_to_llm.application.uc_modify_prompt import ModifyPromptUseCase
from codebase_to_llm.application.uc_remove_api_key import RemoveApiKeyUseCase
from codebase_to_llm.application.uc_remove_model import RemoveModelUseCase
from codebase_to_llm.application.uc_remove_elmts_from_context_buffer import (
    RemoveElementsFromContextBufferUseCase,
)
from codebase_to_llm.application.uc_set_prompt_from_favorite import (
    AddPromptFromFavoriteLisUseCase,
)
from codebase_to_llm.application.uc_update_api_key import UpdateApiKeyUseCase
from codebase_to_llm.application.uc_update_model import UpdateModelUseCase
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
from codebase_to_llm.application.uc_get_model_api_key import (
    GetModelApiKeyUseCase,
)
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.application.uc_get_file import GetFileUseCase
from codebase_to_llm.application.uc_update_file import UpdateFileUseCase
from codebase_to_llm.application.uc_delete_file import DeleteFileUseCase
from codebase_to_llm.application.uc_add_directory import AddDirectoryUseCase
from codebase_to_llm.application.uc_get_directory import GetDirectoryUseCase
from codebase_to_llm.application.uc_update_directory import UpdateDirectoryUseCase
from codebase_to_llm.application.uc_delete_directory import DeleteDirectoryUseCase
from codebase_to_llm.application.uc_register_user import RegisterUserUseCase
from codebase_to_llm.application.uc_authenticate_user import AuthenticateUserUseCase
from codebase_to_llm.application.uc_validate_user import ValidateUserUseCase
from codebase_to_llm.domain.result import Result
from codebase_to_llm.domain.user import User, UserName

from codebase_to_llm.infrastructure.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_model_repository import (
    SqlAlchemyModelRepository,
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
from codebase_to_llm.infrastructure.logging_metrics_service import (
    LoggingMetricsService,
)

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


# FastAPI app with enhanced documentation
app = FastAPI(
    title="Codebase to LLM API",
    description="API for managing codebase context, prompts, and LLM interactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

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
_metrics = LoggingMetricsService()


def get_user_repositories(user: User) -> tuple[
    SqlAlchemyApiKeyRepository,
    SqlAlchemyModelRepository,
    SqlAlchemyRulesRepository,
    SqlAlchemyRecentRepository,
    SqlAlchemyFavoritePromptsRepository,
]:
    """Create user-specific repository instances."""
    user_id = user.id().value()
    return (
        SqlAlchemyApiKeyRepository(user_id),
        SqlAlchemyModelRepository(user_id),
        SqlAlchemyRulesRepository(user_id),
        SqlAlchemyRecentRepository(user_id),
        SqlAlchemyFavoritePromptsRepository(user_id),
    )


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class RegisterRequest(BaseModel):
    user_name: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class AddApiKeyRequest(BaseModel):
    id_value: str
    url_provider: str
    api_key_value: str


class UpdateApiKeyRequest(BaseModel):
    api_key_id: str
    new_url_provider: str
    new_api_key_value: str


class AddModelRequest(BaseModel):
    id_value: str
    name: str
    api_key_id: str


class UpdateModelRequest(BaseModel):
    model_id: str
    new_name: str
    new_api_key_id: str


class AddFileRequest(BaseModel):
    path: str


class AddSnippetRequest(BaseModel):
    path: str
    start: int
    end: int
    text: str


class AddExternalSourceRequest(BaseModel):
    url: str
    include_timestamps: bool = False


class RemoveExternalSourceRequest(BaseModel):
    url: str


class RemoveElementsRequest(BaseModel):
    elements: list[str]


class AddPromptFromFileRequest(BaseModel):
    path: str


class ModifyPromptRequest(BaseModel):
    new_content: str


class SetPromptFromFavoriteRequest(BaseModel):
    content: str


class FavoritePromptCreateRequest(BaseModel):
    name: str
    content: str


class FavoritePromptUpdateRequest(BaseModel):
    id: str
    name: str
    content: str


class FavoritePromptIdRequest(BaseModel):
    id: str


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


class AddFileAsPromptVariableRequest(BaseModel):
    variable_key: str
    relative_path: str


class AddRecentRepositoryPathRequest(BaseModel):
    path: str


class GenerateResponseRequest(BaseModel):
    model_id: str
    include_tree: bool = True
    root_directory_path: str | None = None


class TestMessageRequest(BaseModel):
    model_id: str
    message: str
    previous_response_id: Optional[str] = None  
    stream_format: Literal["sse", "ndjson"] = "sse"  # optional: choose stream wire format


class CopyContextRequest(BaseModel):
    include_tree: bool = True
    root_directory_path: str | None = None


class UploadFileRequest(BaseModel):
    name: str
    content: str
    directory_id: str | None = None


class UpdateFileRequest(BaseModel):
    new_name: str | None = None
    new_directory_id: str | None = None


class CreateDirectoryRequest(BaseModel):
    name: str
    parent_id: str | None = None


class UpdateDirectoryRequest(BaseModel):
    new_name: str | None = None
    new_parent_id: str | None = None


# ============================================================================
# AUTHENTICATION UTILITIES
# ============================================================================


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


# ============================================================================
# UI ROUTES (Static Files)
# ============================================================================

ui_router = APIRouter(tags=["UI"], include_in_schema=False)


@ui_router.get("/")
def serve_web_ui() -> FileResponse:
    """Serve the web UI HTML file."""
    html_file_path = Path(__file__).parent / "web_ui.html"
    return FileResponse(html_file_path, media_type="text/html")


@ui_router.get("/login")
def serve_login_ui() -> FileResponse:
    """Serve the login UI HTML file."""
    html_file_path = Path(__file__).parent / "login.html"
    return FileResponse(html_file_path, media_type="text/html")


@ui_router.get("/register")
def serve_register_ui() -> FileResponse:
    """Serve the registration UI HTML file."""
    html_file_path = Path(__file__).parent / "register.html"
    return FileResponse(html_file_path, media_type="text/html")


@ui_router.get("/favorite-prompts-ui")
def serve_favorite_prompts_ui() -> FileResponse:
    """Serve the favorite prompts management UI."""
    html_file_path = Path(__file__).parent / "favorite_prompts.html"
    return FileResponse(html_file_path, media_type="text/html")


@ui_router.get("/file-manager-test")
def serve_file_manager_test_ui() -> FileResponse:
    """Serve the file and directory manager test interface."""
    html_file_path = Path(__file__).parent / "file_manager_test.html"
    return FileResponse(html_file_path, media_type="text/html")


@ui_router.get("/chat-ui")
def serve_chat_ui() -> FileResponse:
    """Serve the chat UI for testing websocket communication."""
    html_file_path = Path(__file__).parent / "chat_ui.html"
    return FileResponse(html_file_path, media_type="text/html")


@ui_router.get("/web_ui.css")
def serve_css() -> FileResponse:
    """Serve the CSS file."""
    css_file_path = Path(__file__).parent / "web_ui.css"
    return FileResponse(css_file_path, media_type="text/css")


# ============================================================================
# AUTHENTICATION & USER MANAGEMENT
# ============================================================================

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", summary="Register a new user")
def register_user(request: RegisterRequest) -> dict[str, str]:
    """Register a new user account with email validation."""
    use_case = RegisterUserUseCase(_user_repo, _email_sender)
    result = use_case.execute(request.user_name, request.email, request.password)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    user = result.ok()
    assert user is not None
    return {"id": user.id().value(), "user_name": user.name().value()}


@auth_router.get("/validate", summary="Validate user account")
def validate_user(token: str) -> FileResponse:
    """Validate user account using the token from email."""
    use_case = ValidateUserUseCase(_user_repo)
    result = use_case.execute(token)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())

    # Redirect to login page after successful validation
    html_file_path = Path(__file__).parent / "validation_success.html"
    return FileResponse(html_file_path, media_type="text/html")


@auth_router.post("/token", summary="Login and get access token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Authenticate user and return access token."""
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


# ============================================================================
# API KEYS MANAGEMENT
# ============================================================================

api_keys_router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@api_keys_router.post("/", summary="Add a new API key")
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


@api_keys_router.get("/", summary="List all API keys")
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


@api_keys_router.put("/", summary="Update an API key")
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


@api_keys_router.delete("/{api_key_id}", summary="Delete an API key")
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


# ============================================================================
# MODELS MANAGEMENT
# ============================================================================

models_router = APIRouter(prefix="/models", tags=["Models"])


@models_router.post("/", summary="Add a new model")
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


@models_router.get("/", summary="List all models")
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


@models_router.put("/", summary="Update a model")
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


@models_router.delete("/{model_id}", summary="Delete a model")
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


# ============================================================================
# CONTEXT BUFFER MANAGEMENT
# ============================================================================

context_router = APIRouter(prefix="/context-buffer", tags=["Context Buffer"])


@context_router.post("/file", summary="Add file to context buffer")
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


@context_router.post("/snippet", summary="Add code snippet to context buffer")
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


@context_router.post("/external", summary="Add external source to context buffer")
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


@context_router.get("/external", summary="Get external sources")
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


@context_router.delete("/external", summary="Remove external source")
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


@context_router.delete("/external/all", summary="Remove all external sources")
def remove_all_external_sources(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Remove all external sources from the context buffer."""
    use_case = RemoveAllExternalSourcesUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "cleared"}


@context_router.delete("/all", summary="Clear entire context buffer")
def clear_context_buffer(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Clear all content from the context buffer."""
    use_case = ClearContextBufferUseCase(_context_buffer)
    result = use_case.execute()
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "cleared"}


@context_router.delete("/", summary="Remove specific elements from context buffer")
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


@context_router.post("/copy", summary="Copy context to clipboard")
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


# ============================================================================
# PROMPT MANAGEMENT
# ============================================================================

prompt_router = APIRouter(prefix="/prompt", tags=["Prompt Management"])


@prompt_router.post("/from-file", summary="Load prompt from file")
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


@prompt_router.post("/modify", summary="Modify current prompt")
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


@prompt_router.post("/from-favorite", summary="Set prompt from favorite")
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


@prompt_router.post("/variable", summary="Add file as prompt variable")
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


# ============================================================================
# FAVORITE PROMPTS MANAGEMENT
# ============================================================================

favorite_prompts_router = APIRouter(
    prefix="/favorite-prompts", tags=["Favorite Prompts"]
)


@favorite_prompts_router.get("/", summary="Get all favorite prompts")
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


@favorite_prompts_router.get("/{prompt_id}", summary="Get favorite prompt by ID")
def get_favorite_prompt(
    prompt_id: str, current_user: Annotated[User, Depends(get_current_user)]
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


@favorite_prompts_router.post("/", summary="Create a new favorite prompt")
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


@favorite_prompts_router.put("/", summary="Update a favorite prompt")
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


@favorite_prompts_router.delete("/", summary="Delete a favorite prompt")
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


# ============================================================================
# RULES MANAGEMENT
# ============================================================================

rules_router = APIRouter(prefix="/rules", tags=["Rules Management"])


@rules_router.get("/", summary="Get all rules")
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


@rules_router.post("/", summary="Create a new rule")
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


@rules_router.put("/", summary="Update a rule")
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


@rules_router.delete("/", summary="Delete a rule")
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


# ============================================================================
# FILE MANAGEMENT
# ============================================================================

files_router = APIRouter(prefix="/files", tags=["File Management"])


@files_router.post("/", summary="Upload a new file")
def upload_file(
    request: UploadFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Upload a new file to the system."""
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


@files_router.get("/{file_id}", summary="Get file by ID")
def get_file(
    file_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str | None]:
    """Get a file by its ID."""
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


@files_router.put("/{file_id}", summary="Update file")
def update_file(
    file_id: str,
    request: UpdateFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update file metadata."""
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


@files_router.delete("/{file_id}", summary="Delete file")
def delete_file(
    file_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    """Delete a file by its ID."""
    use_case = DeleteFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(current_user.id().value(), file_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}


# ============================================================================
# DIRECTORY MANAGEMENT
# ============================================================================

directories_router = APIRouter(prefix="/directories", tags=["Directory Management"])


@directories_router.post("/", summary="Create a new directory")
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


@directories_router.get("/{directory_id}", summary="Get directory by ID")
def get_directory(
    directory_id: str, current_user: Annotated[User, Depends(get_current_user)]
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


@directories_router.put("/{directory_id}", summary="Update directory")
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


@directories_router.delete("/{directory_id}", summary="Delete directory")
def delete_directory(
    directory_id: str, current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    """Delete a directory by its ID."""
    use_case = DeleteDirectoryUseCase(_directory_structure_repo)
    result = use_case.execute(current_user.id().value(), directory_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}


# ============================================================================
# LLM & CONTEXT OPERATIONS
# ============================================================================

llm_router = APIRouter(prefix="/llm", tags=["LLM Operations"])


@llm_router.post("/response", summary="Generate LLM response")
def generate_llm_response(
    request: GenerateResponseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Generate a response from the LLM using the current context."""
    api_key_repo, model_repo, rules_repo, _, _ = get_user_repositories(current_user)
    model_id_result = ModelId.try_create(request.model_id)
    if model_id_result.is_err():
        raise HTTPException(status_code=400, detail=model_id_result.err())
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None
    use_case = GenerateLLMResponseUseCase()
    result = use_case.execute(
        model_id_obj,
        _llm_adapter,
        model_repo,
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


@llm_router.post("/test-message", summary="Test message generation with a model")
def test_message_generation(
    request: TestMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    api_key_repo, model_repo, _, _, _ = get_user_repositories(current_user)

    model_id_result = ModelId.try_create(request.model_id)
    if model_id_result.is_err():
        raise HTTPException(status_code=400, detail=model_id_result.err())
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None

    details_result = GetModelApiKeyUseCase().execute(model_id_obj, model_repo, api_key_repo)
    if details_result.is_err():
        raise HTTPException(status_code=400, detail=details_result.err())
    details = details_result.ok()
    if details is None:
        raise HTTPException(status_code=404, detail="Model or API key not found")

    model_name, api_key = details

    # Pass through an optional previous_response_id from the request if you support it
    # (add it to your TestMessageRequest pydantic model)
    try:
        response_stream: Result[Stream, str] = _llm_adapter.generate_response(
            request.message,
            model_name,
            api_key,
            previous_response_id=getattr(request, "previous_response_id", None),
        )

        def gen():
            # Optional: send a comment line to open the stream promptly
            yield b": stream-start\n\n"

            stream = response_stream.ok()
            if stream is not None:
                for event in stream:
                    match event:
                        case ResponseTextDeltaEvent(delta=delta):
                            # Send text deltas as SSE data events
                            payload = {"type": "response.output_text.delta", "delta": delta}
                            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")

                        case ResponseCompletedEvent(response=resp):
                            # Final event: includes response.id you'll reuse later
                            usage = getattr(resp, "usage", None)
                            usage_dict = None
                            if usage is not None:
                                # Convert ResponseUsage object to dictionary for JSON serialization
                                usage_dict = {
                                    "completion_tokens": getattr(usage, "completion_tokens", None),
                                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                                    "total_tokens": getattr(usage, "total_tokens", None),
                                }
                            
                            payload = {
                                "type": "response.completed",
                                "response": {
                                    "id": resp.id,
                                    "status": getattr(resp, "status", "completed"),
                                    "usage": usage_dict,
                                    # include anything else you need
                                },
                            }
                            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
                            # Optionally a terminator comment
                            yield b": stream-end\n\n"

                        case _:
                            # ignore other event types or forward them similarly
                            pass

        return StreamingResponse(gen(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


# ============================================================================
# RECENT REPOSITORIES
# ============================================================================

recent_router = APIRouter(prefix="/recent-repositories", tags=["Recent Repositories"])


@recent_router.post("/", summary="Add recent repository path")
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


# ============================================================================
# LEGACY ENDPOINTS (for backward compatibility)
# ============================================================================


# Keep some legacy endpoints for backward compatibility
@app.post("/register")
def register_user_legacy(request: RegisterRequest) -> dict[str, str]:
    """Legacy endpoint - use /auth/register instead."""
    return register_user(request)


@app.get("/validate")
def validate_user_legacy(token: str) -> FileResponse:
    """Legacy endpoint - use /auth/validate instead."""
    return validate_user(token)


@app.post("/token")
def login_for_access_token_legacy(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Legacy endpoint - use /auth/token instead."""
    return login_for_access_token(form_data)


# ============================================================================
# REGISTER ALL ROUTERS
# ============================================================================

app.include_router(ui_router)
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(models_router)
app.include_router(context_router)
app.include_router(prompt_router)
app.include_router(favorite_prompts_router)
app.include_router(rules_router)
app.include_router(files_router)
app.include_router(directories_router)
app.include_router(llm_router)
app.include_router(recent_router)
