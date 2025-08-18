from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["UI"], include_in_schema=False)


@router.get("/")
def serve_web_ui() -> FileResponse:
    """Serve the web UI HTML file."""
    html_file_path = Path(__file__).parent / "web_ui.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.get("/login")
def serve_login_ui() -> FileResponse:
    """Serve the login UI HTML file."""
    html_file_path = Path(__file__).parent / "login.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.get("/register")
def serve_register_ui() -> FileResponse:
    """Serve the registration UI HTML file."""
    html_file_path = Path(__file__).parent / "register.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.get("/favorite-prompts-ui")
def serve_favorite_prompts_ui() -> FileResponse:
    """Serve the favorite prompts management UI."""
    html_file_path = Path(__file__).parent / "favorite_prompts.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.get("/file-manager-test")
def serve_file_manager_test_ui() -> FileResponse:
    """Serve the file and directory manager test interface."""
    html_file_path = Path(__file__).parent / "file_manager_test.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.get("/chat-ui")
def serve_chat_ui() -> FileResponse:
    """Serve the chat UI for testing websocket communication."""
    html_file_path = Path(__file__).parent / "chat_ui.html"
    return FileResponse(html_file_path, media_type="text/html")


@router.get("/web_ui.css")
def serve_css() -> FileResponse:
    """Serve the CSS file."""
    css_file_path = Path(__file__).parent / "web_ui.css"
    return FileResponse(css_file_path, media_type="text/css")
