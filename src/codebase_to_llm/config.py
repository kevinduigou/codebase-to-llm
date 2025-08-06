from __future__ import annotations

import os
from dataclasses import dataclass
from typing_extensions import final


@final
@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application configuration values."""

    database_url: str


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig(database_url=os.getenv("DATABASE_URL", "sqlite:///./users.db"))


CONFIG: AppConfig = load_config()
