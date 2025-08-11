from __future__ import annotations

from typing_extensions import final

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import User, ValidationToken


@final
class ValidateUserUseCase:
    """Use case to validate a user account."""

    __slots__ = ("_user_repo",)
    _user_repo: UserRepositoryPort

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    def execute(self, token_value: str) -> Result[User, str]:
        token_result = ValidationToken.try_create(token_value)
        if token_result.is_err():
            return Err("Invalid token.")
        token = token_result.ok()
        if token is None:
            return Err("Invalid token.")

        repo_result = self._user_repo.find_by_validation_token(token)
        if repo_result.is_err():
            return Err("Invalid token.")
        user = repo_result.ok()
        if user is None:
            return Err("Invalid token.")

        updated_user = user.mark_validated()
        save_result = self._user_repo.validate_user(updated_user)
        if save_result.is_err():
            return Err(save_result.err() or "Failed to validate user.")

        return Ok(updated_user)
