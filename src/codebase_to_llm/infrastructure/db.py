from __future__ import annotations

from typing_extensions import final
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session, sessionmaker

from codebase_to_llm.config import CONFIG

# Convert postgresql:// URLs to postgresql+psycopg:// for psycopg3 compatibility
database_url = CONFIG.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

_engine = create_engine(database_url, pool_pre_ping=True)
_Session = sessionmaker(bind=_engine)

# Shared metadata object for Alembic
Base = MetaData()


def get_engine():
    """Return the global SQLAlchemy engine."""
    return _engine


def get_metadata():
    """Return the shared metadata object."""
    return Base


@final
class DatabaseSessionManager:
    """Creates new SQLAlchemy sessions for each request to avoid transaction issues."""

    __slots__ = ()

    @staticmethod
    def get_session() -> Session:
        """Create a new session for each request to avoid transaction conflicts."""
        return _Session()
