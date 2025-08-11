from codebase_to_llm.application.uc_register_user import RegisterUserUseCase
from codebase_to_llm.application.uc_authenticate_user import AuthenticateUserUseCase
from codebase_to_llm.application.uc_validate_user import ValidateUserUseCase
from codebase_to_llm.application.ports import UserRepositoryPort, EmailSenderPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import (
    EmailAddress,
    User,
    UserName,
    ValidationToken,
)


class InMemoryUserRepository(UserRepositoryPort):
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def add_user(self, user: User) -> Result[None, str]:
        self._users[user.name().value()] = user
        return Ok(None)

    def find_by_name(self, name: UserName) -> Result[User, str]:
        user = self._users.get(name.value())
        if user is None:
            return Err("User not found.")
        return Ok(user)

    def find_by_email(self, email: EmailAddress) -> Result[User, str]:
        for user in self._users.values():
            if user.email().value() == email.value():
                return Ok(user)
        return Err("User not found.")

    def find_by_validation_token(self, token: ValidationToken) -> Result[User, str]:
        for user in self._users.values():
            if user.validation_token().value() == token.value():
                return Ok(user)
        return Err("User not found.")

    def validate_user(self, user: User) -> Result[None, str]:
        self._users[user.name().value()] = user
        return Ok(None)


class FakeEmailSender(EmailSenderPort):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_validation_email(
        self, email: EmailAddress, token: ValidationToken
    ) -> Result[None, str]:
        self.sent.append((email.value(), token.value()))
        return Ok(None)


def test_user_must_validate_before_login() -> None:
    repo = InMemoryUserRepository()
    email_sender = FakeEmailSender()
    register = RegisterUserUseCase(repo, email_sender)
    result = register.execute("alice", "alice@example.com", "secret")
    assert result.is_ok()
    user = result.ok()
    assert user is not None

    auth = AuthenticateUserUseCase(repo)
    assert auth.execute("alice", "secret").is_err()

    token = user.validation_token().value()
    validate = ValidateUserUseCase(repo)
    assert validate.execute(token).is_ok()

    assert auth.execute("alice", "secret").is_ok()
