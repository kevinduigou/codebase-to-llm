from __future__ import annotations

import os
from dataclasses import dataclass
from typing_extensions import final
from dotenv import load_dotenv

# Load environment variables from .env-development file
load_dotenv(".env-development")


@final
@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application configuration values."""

    database_url: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender_name: str
    deployment_url: str


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./users.db"),
        smtp_host=os.getenv("SMTP_HOST", "smtp-relay.brevo.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", "8d421b001@smtp-brevo.com"),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_sender_name=os.getenv("SMTP_SENDER_NAME", "CodeToMarket"),
        deployment_url=os.getenv("DEPLOYMENT_URL", "http://localhost:8000"),
    )


CONFIG: AppConfig = load_config()
