# Database Migrations

This directory contains database migration scripts for the codebase-to-llm application.

## Overview

The application uses SQLAlchemy with PostgreSQL to store:
- User accounts and authentication
- API keys per user
- Favorite prompts per user
- Recent repository paths per user
- Rules per user

## Migration Files

### 001_initial_tables.py
Initial migration that creates all the core tables:

- **users**: User management with id, name, and password_hash
- **api_keys**: API keys storage with composite primary key (id, user_id)
- **favorite_prompts**: User's favorite prompts with composite primary key (id, user_id)
- **recent_repos**: Recent repository paths with composite primary key (user_id, position)
- **rules**: User-defined rules with composite primary key (user_id, name)

## Running Migrations

### Prerequisites
- PostgreSQL database accessible
- Python environment with required dependencies installed (`uv sync`)

### Execute Migration
```bash
# Run the migration script
uv run python scripts/run_migration.py

# Or run the migration directly
uv run python migrations/001_initial_tables.py
```

### Verify Tables
```bash
# Verify that all tables were created successfully
uv run python scripts/verify_tables.py
```

## Database Configuration

The migration scripts use the `DATABASE_URL` environment variable or default to the provided PostgreSQL connection string.

The database URL format for PostgreSQL with psycopg3:
```
postgresql+psycopg://username:password@host:port/database?sslmode=require&channel_binding=require
```


## Creating Update Migration Scripts with Alembic

For production-grade database migrations, we recommend using Alembic, which provides version control for database schemas and handles migration dependencies automatically.

### 1. Install and Initialize Alembic

First, add Alembic to your project dependencies:

```bash
# Add to pyproject.toml dependencies
uv add alembic

# Initialize Alembic in your project
uv run alembic init alembic
```

This creates:
- `alembic/` directory with migration files
- `alembic.ini` configuration file
- `alembic/env.py` environment configuration

### 2. Configure Alembic

Edit `alembic.ini` to set your database URL:

```ini
# alembic.ini
sqlalchemy.url = postgresql+psycopg://...:....@ep-floral-sun-a9f3fit4-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require
```

Or configure it to use environment variables in `alembic/env.py`:

```python
# alembic/env.py
import os
from sqlalchemy import create_engine

# Get database URL from environment or config
database_url = os.getenv('DATABASE_URL') or config.get_main_option("sqlalchemy.url")
```

### 3. Configure Target Metadata

Update `alembic/env.py` to include your SQLAlchemy models:

```python
# alembic/env.py
import sys
from pathlib import Path

# Add your src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import your SQLAlchemy metadata
from codebase_to_llm.infrastructure.sqlalchemy_user_repository import _metadata as user_metadata
from codebase_to_llm.infrastructure.sqlalchemy_api_key_repository import _metadata as api_key_metadata
from codebase_to_llm.infrastructure.sqlalchemy_favorite_prompts_repository import _metadata as prompts_metadata
from codebase_to_llm.infrastructure.sqlalchemy_recent_repository import _metadata as recent_metadata
from codebase_to_llm.infrastructure.sqlalchemy_rules_repository import _metadata as rules_metadata

# Combine all metadata
from sqlalchemy import MetaData
combined_metadata = MetaData()
for metadata in [user_metadata, api_key_metadata, prompts_metadata, recent_metadata, rules_metadata]:
    for table in metadata.tables.values():
        table.tometadata(combined_metadata)

target_metadata = combined_metadata
```

### 4. Generate Initial Migration

Create the initial migration from your existing tables:

```bash
# Generate migration for current state
uv run alembic revision --autogenerate -m "Initial tables"

# This creates a file like: alembic/versions/001_initial_tables.py
```

### 5. Creating Update Migrations

When you need to modify tables, follow these steps:

#### Step 1: Modify Your SQLAlchemy Models
Update your repository files (e.g., add a column to a table):

```python
# In src/codebase_to_llm/infrastructure/sqlalchemy_user_repository.py
_users_table = Table(
    "users",
    _metadata,
    Column("id", String, primary_key=True),
    Column("name", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("email", String, unique=True, nullable=True),  # New column
    Column("created_at", DateTime, default=func.now()),   # New column
)
```

#### Step 2: Generate Migration
```bash
# Auto-generate migration based on model changes
uv run alembic revision --autogenerate -m "Add email and created_at to users"

# This creates: alembic/versions/002_add_email_and_created_at_to_users.py
```

#### Step 3: Review Generated Migration
Alembic will generate something like:

```python
"""Add email and created_at to users

Revision ID: 002_add_email
Revises: 001_initial_tables
Create Date: 2025-01-08 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_add_email'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###
```

#### Step 4: Apply Migration
```bash
# Apply the migration
uv run alembic upgrade head

# Or apply specific migration
uv run alembic upgrade 002_add_email
```

### 6. Common Alembic Commands

```bash
# Show current migration status
uv run alembic current

# Show migration history
uv run alembic history

# Upgrade to latest migration
uv run alembic upgrade head

# Upgrade to specific revision
uv run alembic upgrade 002_add_email

# Downgrade one revision
uv run alembic downgrade -1

# Downgrade to specific revision
uv run alembic downgrade 001_initial_tables

# Show SQL that would be executed (dry run)
uv run alembic upgrade head --sql

# Generate empty migration file for manual changes
uv run alembic revision -m "Custom migration"
```

### 7. Manual Migration Examples

For complex changes that auto-generation can't handle:

```python
"""Custom migration example

Revision ID: 003_custom_changes
Revises: 002_add_email
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add index
    op.create_index('idx_users_email_active', 'users', ['email'], 
                   postgresql_where=sa.text('email IS NOT NULL'))
    
    # Migrate data
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE users SET created_at = NOW() WHERE created_at IS NULL
    """))
    
    # Add constraint
    op.alter_column('users', 'created_at', nullable=False)

def downgrade() -> None:
    op.alter_column('users', 'created_at', nullable=True)
    op.drop_index('idx_users_email_active')
```

### 8. Production Migration Workflow

```bash
# 1. Develop and test migration locally
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head

# 2. Test rollback
uv run alembic downgrade -1
uv run alembic upgrade head

# 3. Deploy to staging
export DATABASE_URL="postgresql+psycopg://staging_url"
uv run alembic upgrade head

# 4. Deploy to production (with backup!)
export DATABASE_URL="postgresql+psycopg://production_url"
# Always backup first!
uv run alembic upgrade head
```

### 9. Integration with Existing Scripts

Update your migration runner to use Alembic:

```python
# scripts/run_alembic_migration.py
#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://...:...@ep-floral-sun-a9f3fit4-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    
    # Set environment variable for Alembic
    os.environ["DATABASE_URL"] = database_url
    
    try:
        # Run Alembic upgrade
        result = subprocess.run(["uv", "run", "alembic", "upgrade", "head"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations applied successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 10. Best Practices with Alembic

- **Always review auto-generated migrations** before applying
- **Test migrations on a copy of production data**
- **Keep migrations small and focused**
- **Never edit applied migration files**
- **Always backup before production migrations**
- **Use `--sql` flag to review SQL before applying**
- **Test both upgrade and downgrade paths**
- **Use meaningful migration messages**

## Notes

- All tables use composite primary keys where appropriate to ensure data isolation per user
- The migration is idempotent - running it multiple times won't cause issues
- Tables are created using SQLAlchemy's `metadata.create_all()` which only creates missing tables
- For production systems, consider migrating to Alembic for better version control and rollback capabilities
