"""Low-level avatar provider using Gravatar integration."""

from typing import Optional

from libgravatar import Gravatar  # type: ignore

from src.config import app_config
from .errors import GravatarResolveError


class GravatarProvider:
    """Handles external Gravatar avatars service."""

    GRAVATAR_BASE_URL = "https://www.gravatar.com/avatar/"

    # TODO: Evaluate fallback to avatar served from server static folder
    # May occur when failed to resolve Gravatar -> return None and such case
    # should be solved by frontend. However we may send default avatar image
    # either from server static folder (more suitable fro SSR) or default avatar
    # pre-uploaded to the cloud beforehand

    def resolve_default_avatar_or_none(self, email: str) -> Optional[str]:
        """
        Returns Gravatar image URL for the given email.

        Note:
            This does NOT perform an HTTP request. The URL can be used
            directly in <img> tags or for further HTTP fetch elsewhere.
        """
        if not email:
            return None

        try:
            gravatar = Gravatar(email)
            return gravatar.get_image(size=app_config.AVATAR_IMAGE_SIZE, use_ssl=True)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise GravatarResolveError(
                f"Failed to fetch Gravatar for email={email}"
            ) from exc

    @staticmethod
    def is_gravatar_avatar(url: Optional[str]) -> bool:
        """Check if the given URL is a Gravatar URL."""
        if not url:
            return False
        return url.startswith(GravatarProvider.GRAVATAR_BASE_URL)
