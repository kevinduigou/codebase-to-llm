from __future__ import annotations

from celery import Celery
from codebase_to_llm.config import CONFIG

# Create the main Celery app
celery_app = Celery(
    "codebase_to_llm",
    broker=CONFIG.redis_url,
    backend=CONFIG.redis_url,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Task results expire after 1 hour (3600 seconds)
)

# Import task modules to register tasks (must be after app creation)
# This will register the tasks with the celery_app instance
try:
    import codebase_to_llm.infrastructure.celery_download_queue  # noqa: F401
    import codebase_to_llm.infrastructure.celery_add_subtitle_queue  # noqa: F401
    import codebase_to_llm.infrastructure.celery_key_insights_queue  # noqa: F401
    import codebase_to_llm.infrastructure.celery_video_summary_queue  # noqa: F401
except ImportError as e:
    # Log the error but don't fail - some tasks might not be available in all environments
    import logging

    logging.getLogger(__name__).warning(f"Could not import task modules: {e}")
