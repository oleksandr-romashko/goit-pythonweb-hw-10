"""Workflow to send email verification message"""

from fastapi import BackgroundTasks
from src.services.auth_service import AuthService
from src.services.mail_service import MailService
from src.services.dtos import UserDTO


def send_verification_email(
    *,
    target_user: UserDTO,
    base_url: str,
    auth_service: AuthService,
    mail_service: MailService,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Orchestrates sending of email verification message.

    Application-level helper.
    """

    # Note: token is not persistent (no side-effects in database),
    #       still it is more safe and best practice to to handle its creation
    #       outside of background_tasks, where email is actually sent
    token = auth_service.create_email_confirmation_token(
        target_user.id,
        target_user.email,
    )

    background_tasks.add_task(
        mail_service.send_registration_welcome_email,
        target_user.id,
        target_user.email,
        target_user.username,
        base_url,
        token,
    )
