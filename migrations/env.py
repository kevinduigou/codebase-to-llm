import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the project root to Python path for imports before importing our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Now we can import our modules
from src.codebase_to_llm.infrastructure.db import Base

# Import all repositories to ensure tables are registered
# These imports are necessary for Alembic to detect the tables
from src.codebase_to_llm.infrastructure import sqlalchemy_user_repository  # noqa: F401
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_api_key_repository,  # noqa: F401
)
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_favorite_prompts_repository,  # noqa: F401
)
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_recent_repository,  # noqa: F401
)
from src.codebase_to_llm.infrastructure import sqlalchemy_rules_repository  # noqa: F401
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_directory_repository,  # noqa: F401
)
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_file_repository,  # noqa: F401
)
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_model_repository,  # noqa: F401
)
from src.codebase_to_llm.infrastructure import (
    sqlalchemy_video_key_insights_repository,  # noqa: F401
)

# Load environment variables from .env-development file
load_dotenv(".env-development")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

target_metadata = Base

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    # Convert postgresql:// URLs to postgresql+psycopg:// for psycopg3 compatibility
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override the sqlalchemy.url with DATABASE_URL if available
    configuration = config.get_section(config.config_ini_section, {})
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Convert postgresql:// URLs to postgresql+psycopg:// for psycopg3 compatibility
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
