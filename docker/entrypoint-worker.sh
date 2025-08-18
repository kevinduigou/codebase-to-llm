#!/bin/bash
set -e

echo "Starting Celery worker..."
exec uv run celery -A codebase_to_llm.infrastructure.celery_download_queue worker --loglevel=info
