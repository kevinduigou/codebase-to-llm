from __future__ import annotations

from typing_extensions import final
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from codebase_to_llm.config import CONFIG

_engine = create_engine(CONFIG.database_url, pool_pre_ping=True)
_Session = sessionmaker(bind=_engine)
_session: Session | None = None


def get_engine():
    """Return the global SQLAlchemy engine."""
    return _engine


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
