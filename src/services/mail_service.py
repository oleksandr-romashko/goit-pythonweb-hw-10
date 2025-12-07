"""Email service module for sending emails."""

from datetime import datetime

from fastapi_mail import MessageSchema, MessageType, NameEmail

from src.providers.mail_provider import MailProvider, FastMailProvider
from src.utils.logger import logger


class MailService:
    """Handles email sending functionalities."""

    def __init__(self, mail_provider: MailProvider):
        """Initialize the service with mail provider."""
        self.mail_provider = mail_provider

    async def send_registration_welcome_email(
        self,
        user_id: int,
        email: str,
        username: str,
        host: str,
        verification_token: str,
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
            await self.mail_provider.send_message(
                message,
                template_name="registration_welcome_email.html",
            )
            logger.info(
                "Sent registration welcome email to user with user_id=%s", user_id
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "Failed to send registration welcome email for user with user_id=%s: %s",
                user_id,
                str(exc),
            )
            return


mail_service = MailService(mail_provider=FastMailProvider())
"""Default MailService instance."""
