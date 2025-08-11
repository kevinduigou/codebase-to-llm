from __future__ import annotations

from typing_extensions import final

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import User, UserName, EmailAddress


@final
class AuthenticateUserUseCase:
    """Use case to authenticate a user."""

    __slots__ = ("_user_repo",)
    _user_repo: UserRepositoryPort

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    def execute(self, username_or_email: str, password: str) -> Result[User, str]:
        # Try to find user by username first
        name_result = UserName.try_create(username_or_email)
        if name_result.is_ok():
            name = name_result.ok()
            if name is not None:
                repo_result = self._user_repo.find_by_name(name)
                if repo_result.is_ok():
                    user = repo_result.ok()
                    if user is not None and user.verify_password(password):
                        if not user.is_validated():
                            return Err("Account not validated.")
                        return Ok(user)

        # Try to find user by email if username lookup failed
        email_result = EmailAddress.try_create(username_or_email)
        if email_result.is_ok():
            email = email_result.ok()
            if email is not None:
                repo_result = self._user_repo.find_by_email(email)
                if repo_result.is_ok():
                    user = repo_result.ok()
                    if user is not None and user.verify_password(password):
                        if not user.is_validated():
                            return Err("Account not validated.")
                        return Ok(user)

        return Err("Invalid credentials.")
