from __future__ import annotations

from typing_extensions import final

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import User, UserName


@final
class AuthenticateUserUseCase:
    """Use case to authenticate a user."""

    __slots__ = ("_user_repo",)
    _user_repo: UserRepositoryPort

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    def execute(self, user_name: str, password: str) -> Result[User, str]:
        name_result = UserName.try_create(user_name)
        if name_result.is_err():
            return Err("Invalid username.")

        name = name_result.ok()
        if name is None:
            return Err("Invalid username.")

        repo_result = self._user_repo.find_by_name(name)
        if repo_result.is_err():
            return Err("User not found.")

        user = repo_result.ok()
        if user is None or not user.verify_password(password):
            return Err("Invalid credentials.")

        return Ok(user)
