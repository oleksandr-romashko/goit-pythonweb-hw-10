"""Low-level mail provider using FastMail integration."""

from abc import ABC, abstractmethod
from typing import Optional

from fastapi_mail import (
    FastMail,
    ConnectionConfig,
    MessageSchema,
)

from src.config import app_config


class MailProvider(ABC):
    """Abstract class for a mail provider"""

    @abstractmethod
    async def send_message(self, message: MessageSchema, template_name: str) -> None:
        """Send mail message."""


class FastMailProvider(MailProvider):
    """Low-level provider to send emails using FastMail."""

    def __init__(self, conf: Optional[ConnectionConfig] = None):
        self.fastmail_config: ConnectionConfig = ConnectionConfig(
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
        self.fm = FastMail(conf or self.fastmail_config)

    async def send_message(self, message: MessageSchema, template_name: str):
        """Send email message via FastMail."""
        await self.fm.send_message(message, template_name=template_name)
