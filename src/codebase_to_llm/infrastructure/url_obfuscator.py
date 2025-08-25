"""URL obfuscation utility for logging sensitive connection strings."""

from __future__ import annotations

import re
from typing_extensions import final


@final
class UrlObfuscator:
    """Utility class for obfuscating passwords in URLs."""

    @staticmethod
    def obfuscate_url(url: str) -> str:
        """
        Obfuscate password in a URL for safe logging.

        Args:
            url: The URL to obfuscate (e.g., "redis://user:password@host:port/db")

        Returns:
            URL with password replaced by asterisks

        Examples:
            >>> UrlObfuscator.obfuscate_url("redis://default:mypassword@host:6379/0")
            "redis://default:***@host:6379/0"
            >>> UrlObfuscator.obfuscate_url("postgresql://user:secret@localhost:5432/db")
            "postgresql://user:***@localhost:5432/db"
        """
        if not url:
            return url

        # Pattern to match URLs with credentials: scheme://user:password@host:port/path
        pattern = r"(^[^:]+://[^:]+:)([^@]+)(@.+)"

        def replace_password(match: re.Match[str]) -> str:
            prefix = match.group(1)  # scheme://user:
            password = match.group(2)  # password
            suffix = match.group(3)  # @host:port/path

            # Replace password with asterisks (minimum 3, maximum length of original)
            obfuscated = "*" * min(max(3, len(password)), 10)
            return f"{prefix}{obfuscated}{suffix}"

        return re.sub(pattern, replace_password, url)
