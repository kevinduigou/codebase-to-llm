from __future__ import annotations

from typing_extensions import final
from uuid import uuid4

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import User


@final
class RegisterUserUseCase:
    """Use case to register a new user."""

    __slots__ = ("_user_repo",)
    _user_repo: UserRepositoryPort

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    def execute(self, user_name: str, password: str) -> Result[User, str]:
        user_result = User.try_create(str(uuid4()), user_name, password)
        if user_result.is_err():
            return Err("Invalid user.")

        user = user_result.ok()
        if user is None:
            return Err("User creation failed.")

        save_result = self._user_repo.add_user(user)
        if save_result.is_err():
            return Err(save_result.err())

        return Ok(user)
