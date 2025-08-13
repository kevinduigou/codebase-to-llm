from __future__ import annotations

from typing_extensions import final

from codebase_to_llm.application.ports import MetricsPort
from codebase_to_llm.domain.result import Ok, Result
from codebase_to_llm.domain.user import UserName


@final
class LoggingMetricsService(MetricsPort):
    """Simple metrics service that logs token usage."""

    def record_tokens(self, user: UserName, tokens: int) -> Result[None, str]:
        print(f"User {user.value()} used {tokens} tokens")
        return Ok(None)
