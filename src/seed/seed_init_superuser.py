"""Script to init app with superuser"""

import asyncio
import os
import sys

from src.db import session_manager
from src.services import UserService
from src.services.errors import InvalidUserCredentialsError, UserConflictError
from src.utils.logger import logger


async def ensure_superuser_exists() -> None:
    """Ensure superuser exists"""
    username = os.getenv("SUPERADMIN_USERNAME", "superadmin")
    email = os.getenv("SUPERADMIN_EMAIL", "")
    password = os.getenv("SUPERADMIN_PASSWORD", "")

    async with session_manager.session() as db_session:
        user_service = UserService(db_session)

        try:
            await user_service.create_superuser(username, email, password)
            logger.info("✔ Superuser created.")
        except InvalidUserCredentialsError as e:
            logger.error("✘ Failed to create superuser: %s", str(e))
            sys.exit(1)
        except UserConflictError:
            logger.debug("✔ Superuser already exists. No action needed.")


if __name__ == "__main__":
    asyncio.run(ensure_superuser_exists())
