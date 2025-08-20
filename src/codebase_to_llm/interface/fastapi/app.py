from __future__ import annotations

import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv

from .schemas import RegisterRequest, Token
from .auth import (
    router as auth_router,
    register_user,
    validate_user,
    login_for_access_token,
)
from .ui import router as ui_router
from .api_keys import router as api_keys_router
from .models import router as models_router
from .context_buffer import router as context_router
from .prompt import router as prompt_router
from .favorite_prompts import router as favorite_prompts_router
from .rules import router as rules_router
from .files import router as files_router
from .directories import router as directories_router
from .llm import router as llm_router
from .recent import router as recent_router
from .downloads import router as downloads_router
from .translations import router as translations_router
from .key_insights import router as key_insights_router

load_dotenv(".env-development")

app = FastAPI(
    title="Codebase to LLM API",
    description="API for managing codebase context, prompts, and LLM interactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

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
app.include_router(downloads_router)
app.include_router(translations_router)
app.include_router(key_insights_router)


@app.post("/register")
def register_user_legacy(request: RegisterRequest) -> dict[str, str]:
    return register_user(request)


@app.get("/validate")
def validate_user_legacy(token: str) -> FileResponse:
    return validate_user(token)


@app.post("/token")
def login_for_access_token_legacy(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    return login_for_access_token(form_data)
