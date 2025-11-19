"""Email service module for sending emails."""

from datetime import datetime

from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
    MessageType,
    NameEmail,
)

from src.config import app_config
from src.utils.logger import logger


class MailService:
    """Handles email sending functionalities."""

    def __init__(self):
        """Initialize the service with a email configuration."""
        self.conf = ConnectionConfig(
            MAIL_SERVER=app_config.MAIL_SERVER,
            MAIL_PORT=int(app_config.MAIL_PORT),
            MAIL_USERNAME=app_config.MAIL_USERNAME,
            MAIL_PASSWORD=app_config.MAIL_PASSWORD,
            MAIL_FROM=app_config.MAIL_FROM,
            MAIL_FROM_NAME=app_config.MAIL_FROM_NAME,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=app_config.template_dir,
        )
        self.fm = FastMail(self.conf)

    async def send_registration_welcome_email(
        self, email: str, username: str, host: str, verification_token: str
    ) -> None:
        """Send a welcome email to a newly registered user."""
        logo_url = f"{host}static/images/logo.svg"
        verify_url = f"{host}api/auth/verify-email?token={verification_token}"
        message = MessageSchema(
            recipients=[NameEmail(username, email)],
            subject="Verify your email address",
            template_body={
                "logo_url": logo_url,
                "fullname": username,
                "verify_url": verify_url,
                "current_year": datetime.now().year,
            },
            subtype=MessageType.html,
            alternative_body=f"Hi {username}, confirm your email: {verify_url}",
        )

        try:
            await self.fm.send_message(
                message,
                template_name="registration_welcome_email.html",
            )
            logger.info(
                "Sent registration welcome email to user with username=%s", username
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "Failed to send registration welcome email to %s (username=%s): %s",
                email,
                username,
                exc,
            )
            return
