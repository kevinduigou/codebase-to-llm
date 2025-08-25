"""Behave environment configuration for video key insights tests."""

import os
import requests
import time
from typing import Any
from dotenv import load_dotenv

# Load environment variables from .env-development
load_dotenv(".env-development")


def before_all(context: Any) -> None:
    """Set up test environment before all tests."""
    # Configure base URL for the FastAPI server
    context.base_url = os.getenv("TEST_BASE_URL", "http://localhost:8000")

    # Wait for server to be ready (optional)
    wait_for_server(context.base_url)


def before_scenario(context: Any, scenario: Any) -> None:
    """Set up before each scenario."""
    # Reset context variables
    context.test_user = None
    context.access_token = None
    context.auth_headers = None
    context.test_video_key_insights = None
    context.created_video_key_insights = None
    context.video_key_insights_id = None
    context.retrieved_video_key_insights = None
    context.all_video_key_insights = None

    # Response objects
    context.create_response = None
    context.get_response = None
    context.list_response = None
    context.delete_response = None
    context.get_deleted_response = None


def after_scenario(context: Any, scenario: Any) -> None:
    """Clean up after each scenario."""
    # Clean up any created video key insights if test failed
    if hasattr(context, "video_key_insights_id") and context.video_key_insights_id:
        if hasattr(context, "auth_headers") and context.auth_headers:
            try:
                requests.delete(
                    f"{context.base_url}/key-insights/video-key-insights/{context.video_key_insights_id}",
                    headers=context.auth_headers,
                )
            except Exception:
                # Ignore cleanup errors
                pass


def wait_for_server(base_url: str, timeout: int = 30) -> None:
    """Wait for the FastAPI server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"Server is ready at {base_url}")
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

    print(f"Warning: Server at {base_url} may not be ready")
