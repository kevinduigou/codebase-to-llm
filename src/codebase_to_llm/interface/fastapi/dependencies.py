from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, final

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

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
from codebase_to_llm.infrastructure.celery_download_queue import (
    CeleryDownloadTaskQueue,
)

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


# Shared repositories and services
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
_download_task_queue = CeleryDownloadTaskQueue()


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


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
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


def get_download_task_port() -> CeleryDownloadTaskQueue:
    return _download_task_queue
