from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing_extensions import final

from codebase_to_llm.application.ports import EmailSenderPort
from codebase_to_llm.config import CONFIG
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.user import EmailAddress, ValidationToken


@final
class BrevoEmailSender(EmailSenderPort):
    """SMTP implementation using Brevo server."""

    __slots__ = ()

    def send_validation_email(
        self, email: EmailAddress, token: ValidationToken
    ) -> Result[None, str]:
        message = EmailMessage()
        message["Subject"] = "Account validation"
        message["From"] = CONFIG.smtp_username
        message["To"] = email.value()
        message.set_content(f"Use this token to validate your account: {token.value()}")
        try:
            with smtplib.SMTP(CONFIG.smtp_host, CONFIG.smtp_port) as server:
                server.starttls()
                if CONFIG.smtp_username and CONFIG.smtp_password:
                    server.login(CONFIG.smtp_username, CONFIG.smtp_password)
                server.send_message(message)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
