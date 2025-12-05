"""Service layer providing business logic for managing Contact entities."""

from typing import Optional, Any, List, Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contact
from src.db.repository import ContactsRepository
from src.providers.cache_provider.contact_cache import (
    ContactsCountUserRedisCacheProvider,
)
from src.utils.logger import logger
from src.utils.query_helpers import get_pagination


class ContactService:
    """Handles business logic related to contacts."""

    def __init__(
        self,
        db_session: AsyncSession,
        count_per_user_cache: Optional[ContactsCountUserRedisCacheProvider] = None,
    ):
        """Initialize the service with a contacts repository."""
        self.repo = ContactsRepository(db_session)
        self.count_per_user_cache = count_per_user_cache

    async def create_contact(self, user_id: int, data: Dict[str, Any]) -> Contact:
        """Create a new contact for a given user."""
        contact = await self.repo.create_contact(user_id, data)

        # Delete user contacts count cache
        if self.count_per_user_cache:
            await self.count_per_user_cache.invalidate_contacts_count(user_id)

        return contact

    async def get_all_contacts(
        self, user_id: int, pagination: Dict[str, int], filters: Dict[str, Any]
    ) -> Tuple[List[Contact], int]:
        """Return a paginated list of contacts with applied optional filters."""
        # Check if there are contacts
        total_count = await self.repo.get_contacts_total_count(user_id)
        if total_count == 0:
            return [], 0

        # Get all existing contacts
        skip, limit = get_pagination(pagination)
        contacts: List[Contact] = await self.repo.get_all_contacts(
            user_id, skip, limit, **filters
        )

        return contacts, total_count

    async def get_contacts_count(self, user_id: int) -> int:
        """Return the total number of contacts for a user."""
        # 1. Try get user from cache
        if self.count_per_user_cache:
            contacts_count_cached: Optional[int] = (
                await self.count_per_user_cache.get_contacts_count(user_id)
            )
            if contacts_count_cached is not None:
                logger.debug(
                    "[CACHE HIT] User contacts count for user_id=%s",
                    user_id,
                )
                return contacts_count_cached
            logger.debug("[CACHE MISS] User contacts count for user_id=%s", user_id)
        else:
            logger.debug("[CACHE ERROR] User contacts count cache is disabled")

        # 2. If not in cache --> request from DB
        contacts_count = await self.repo.get_contacts_total_count(user_id)

        # 3. Save to cache
        if self.count_per_user_cache:
            await self.count_per_user_cache.set_contacts_count(user_id, contacts_count)

        return contacts_count

    async def get_contacts_upcoming_birthdays(
        self, user_id: int, pagination: Dict[str, int]
    ) -> Tuple[List[Dict], int]:
        """Return a paginated list of contacts with upcoming birthdays."""
        skip, limit = get_pagination(pagination)
        return await self.repo.get_contacts_upcoming_birthdays(user_id, skip, limit)

    async def get_contact_by_id(
        self, user_id: int, contact_id: int
    ) -> Optional[Contact]:
        """Return a single contact by its ID, or None if not found."""
        return await self.repo.get_contact_by_id(user_id, contact_id)

    async def update_contact_by_id(
        self, user_id: int, contact_id: int, data: Dict[str, Any]
    ) -> Optional[Contact]:
        """Update a contact fully or partially."""
        return await self.repo.update_contact_by_id(user_id, contact_id, data)

    async def remove_contact(self, user_id: int, contact_id: int) -> Optional[Contact]:
        """Delete a contact by ID."""
        contact = await self.repo.remove_contact_by_id(user_id, contact_id)

        # Delete user contacts count cache
        if self.count_per_user_cache:
            await self.count_per_user_cache.invalidate_contacts_count(user_id)

        return contact
