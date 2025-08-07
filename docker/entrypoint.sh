#!/bin/bash
set -e

# Create data directory if it doesn't exist
mkdir -p /app/data

# Initialize database tables if needed
echo "Initializing database..."
uv run python -c "
from codebase_to_llm.infrastructure.db import get_engine
from codebase_to_llm.domain.user import User
from sqlalchemy import text

engine = get_engine()

# Create tables if they don't exist
with engine.connect() as conn:
    # Check if users table exists
    result = conn.execute(text(\"SELECT name FROM sqlite_master WHERE type='table' AND name='users';\"))
    if not result.fetchone():
        print('Creating users table...')
        conn.execute(text('''
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        '''))
        conn.commit()
        print('Users table created successfully.')
    else:
        print('Users table already exists.')
"

echo "Starting FastAPI application..."
exec uv run uvicorn codebase_to_llm.interface.http_api:app --host 0.0.0.0 --port 8000
