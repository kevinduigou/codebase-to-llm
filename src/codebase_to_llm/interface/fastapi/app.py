from __future__ import annotations

import logging
import os
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv

from ...config import CONFIG
from ...infrastructure.url_obfuscator import UrlObfuscator

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
from .add_subtitles import router as add_subtitles_router
from .video_subtitles import router as video_subtitles_router
from .burn_ass import router as burn_ass_router
from .key_insights import router as key_insights_router
from .video_summary import router as video_summary_router
from .stream import router as stream_router

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

@app.middleware("http")
async def add_csp_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "connect-src 'self' https: http://127.0.0.1:8000 ws://127.0.0.1:8000;"
    )
    return response

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
app.include_router(add_subtitles_router)
app.include_router(video_subtitles_router)
app.include_router(burn_ass_router)
app.include_router(key_insights_router)
app.include_router(video_summary_router)
app.include_router(stream_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Log startup information with obfuscated sensitive data."""
    logger = logging.getLogger("uvicorn.error")

    # Log database URL with obfuscated password
    obfuscated_db_url = UrlObfuscator.obfuscate_url(CONFIG.database_url)
    logger.info(f"DATABASE_URL: {obfuscated_db_url}")

    # Log Redis URL with obfuscated password
    obfuscated_redis_url = UrlObfuscator.obfuscate_url(CONFIG.redis_url)
    logger.info(f"REDIS_URL: {obfuscated_redis_url}")


@app.post("/register")
def register_user_legacy(request: RegisterRequest) -> dict[str, str]:
    return register_user(request)


@app.get("/validate")
def validate_user_legacy(token: str) -> FileResponse:
    return validate_user(token)


@app.post("/token")
def login_for_access_token_legacy(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    return login_for_access_token(request, form_data)
