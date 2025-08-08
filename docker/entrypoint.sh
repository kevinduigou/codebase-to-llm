#!/bin/bash
set -e

# Create data directory if it doesn't exist
mkdir -p /app/data

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting FastAPI application..."
exec uv run uvicorn codebase_to_llm.interface.http_api:app --host 0.0.0.0 --port 8000
