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
_session: Session | None = None

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
    """Maintains a single SQLAlchemy session for performance."""

    __slots__ = ()

    @staticmethod
    def get_session() -> Session:
        global _session
        if _session is None or not _session.is_active:
            _session = _Session()
        return _session
