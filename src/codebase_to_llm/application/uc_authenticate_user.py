from __future__ import annotations

import logging
from typing_extensions import final

from codebase_to_llm.application.ports import UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import User, UserName, EmailAddress


@final
class AuthenticateUserUseCase:
    """Use case to authenticate a user."""

    __slots__ = ("_user_repo", "_logger")
    _user_repo: UserRepositoryPort
    _logger: logging.Logger

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo
        self._logger = logging.getLogger(__name__)

    def execute(self, username_or_email: str, password: str) -> Result[User, str]:
        self._logger.debug(
            f"Starting authentication process for identifier: {username_or_email}"
        )

        # Try to find user by username first
        name_result = UserName.try_create(username_or_email)
        if name_result.is_ok():
            name = name_result.ok()
            if name is not None:
                self._logger.debug(f"Attempting username lookup for: {name.value()}")
                repo_result = self._user_repo.find_by_name(name)
                if repo_result.is_ok():
                    user = repo_result.ok()
                    if user is not None:
                        self._logger.debug(
                            f"User found by username: {user.name().value()} (ID: {user.id().value()})"
                        )
                        if user.verify_password(password):
                            if not user.is_validated():
                                self._logger.warning(
                                    f"Authentication failed - account not validated for user: {user.name().value()}"
                                )
                                return Err("Account not validated.")
                            self._logger.info(
                                f"Authentication successful for user: {user.name().value()} via username lookup"
                            )
                            return Ok(user)
                        else:
                            self._logger.warning(
                                f"Authentication failed - invalid password for user: {user.name().value()}"
                            )
                    else:
                        self._logger.debug(
                            f"No user found with username: {name.value()}"
                        )
                else:
                    self._logger.debug(
                        f"Repository error during username lookup: {repo_result.err()}"
                    )

        # Try to find user by email if username lookup failed
        email_result = EmailAddress.try_create(username_or_email)
        if email_result.is_ok():
            email = email_result.ok()
            if email is not None:
                self._logger.debug(f"Attempting email lookup for: {email.value()}")
                repo_result = self._user_repo.find_by_email(email)
                if repo_result.is_ok():
                    user = repo_result.ok()
                    if user is not None:
                        self._logger.debug(
                            f"User found by email: {user.name().value()} (ID: {user.id().value()})"
                        )
                        if user.verify_password(password):
                            if not user.is_validated():
                                self._logger.warning(
                                    f"Authentication failed - account not validated for user: {user.name().value()}"
                                )
                                return Err("Account not validated.")
                            self._logger.info(
                                f"Authentication successful for user: {user.name().value()} via email lookup"
                            )
                            return Ok(user)
                        else:
                            self._logger.warning(
                                f"Authentication failed - invalid password for user: {user.name().value()}"
                            )
                    else:
                        self._logger.debug(f"No user found with email: {email.value()}")
                else:
                    self._logger.debug(
                        f"Repository error during email lookup: {repo_result.err()}"
                    )
        else:
            self._logger.debug(
                f"Invalid email format for identifier: {username_or_email}"
            )

        self._logger.warning(
            f"Authentication failed - invalid credentials for identifier: {username_or_email}"
        )
        return Err("Invalid credentials.")
