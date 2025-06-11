from __future__ import annotations

from typing import Final, List

from domain.result import Result, Err, Ok
from domain.ignore_tokens import IgnoreTokens
from .ports import IgnoreRepositoryPort


class IgnoreService:
    """Application service for persisting ignore tokens."""

    __slots__ = ("_repo",)

    def __init__(self, repo: IgnoreRepositoryPort) -> None:
        self._repo: Final = repo

    def load_tokens(self) -> Result[List[str], str]:
        return self._repo.load_tokens()

    def save_tokens(self, raw_tokens: List[str]) -> Result[None, str]:
        tokens_result = IgnoreTokens.try_create(raw_tokens)
        if tokens_result.is_err():
            return Err(tokens_result.err())  # type: ignore[arg-type]
        tokens = tokens_result.ok()
        if tokens is None:
            return Err("Failed to create ignore tokens")
        return self._repo.save_tokens(list(tokens.tokens()))
