from __future__ import annotations

from typing_extensions import final
from uuid import uuid4

from codebase_to_llm.application.ports import EmailSenderPort, UserRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import User


@final
class RegisterUserUseCase:
    """Use case to register a new user."""

    __slots__ = ("_user_repo", "_email_sender")
    _user_repo: UserRepositoryPort
    _email_sender: EmailSenderPort

    def __init__(
        self, user_repo: UserRepositoryPort, email_sender: EmailSenderPort
    ) -> None:
        self._user_repo = user_repo
        self._email_sender = email_sender

    def execute(self, user_name: str, email: str, password: str) -> Result[User, str]:
        token = str(uuid4())
        user_result = User.try_create(str(uuid4()), user_name, email, password, token)
        if user_result.is_err():
            return Err("Invalid user.")

        user = user_result.ok()
        if user is None:
            return Err("User creation failed.")

        save_result = self._user_repo.add_user(user)
        if save_result.is_err():
            error_msg = save_result.err()
            return Err(error_msg if error_msg is not None else "Failed to save user.")

        email_result = self._email_sender.send_validation_email(
            user.email(), user.validation_token()
        )
        if email_result.is_err():
            return Err(email_result.err() or "Failed to send validation email.")

        return Ok(user)
