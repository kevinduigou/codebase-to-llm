from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm

from codebase_to_llm.application.uc_register_user import RegisterUserUseCase
from codebase_to_llm.application.uc_authenticate_user import AuthenticateUserUseCase
from codebase_to_llm.application.uc_validate_user import ValidateUserUseCase

from .dependencies import (
    _email_sender,
    _user_repo,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from .schemas import RegisterRequest, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", summary="Register a new user")
def register_user(request: RegisterRequest) -> dict[str, str]:
    """Register a new user account with email validation."""
    use_case = RegisterUserUseCase(_user_repo, _email_sender)
    result = use_case.execute(request.user_name, request.email, request.password)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    user = result.ok()
    assert user is not None
    return {"id": user.id().value(), "user_name": user.name().value()}


@router.get("/validate", summary="Validate user account")
def validate_user(token: str) -> FileResponse:
    """Validate user account using the token from email."""
    use_case = ValidateUserUseCase(_user_repo)
    result = use_case.execute(token)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    html_file_path = Path(__file__).parent / "validation_success.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.post("/token", summary="Login and get access token")
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
