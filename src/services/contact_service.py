"""Service layer providing business logic for managing Contact entities."""

from typing import Optional, Any, List, Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contact
from src.db.repository import ContactsRepository


class ContactService:
    """Handles business logic related to contacts."""

    def __init__(self, db_session: AsyncSession):
        """Initialize the service with a contacts repository."""
        self.repo = ContactsRepository(db_session)

    async def create_contact(self, user_id: int, data: Dict[str, Any]) -> Contact:
        """Create a new contact for a given user."""
        return await self.repo.create_contact(user_id, data)

    async def get_all_contacts(
        self, user_id: int, pagination: Dict[str, int], filters: Dict[str, Any]
    ) -> Tuple[List[Contact], int]:
        """Return a paginated list of contacts with optional filters."""
        # Check if there are contacts
        total_count = await self.repo.get_contacts_total_count(user_id)
        if total_count == 0:
            return [], 0

        # Get all existing contacts
        contacts: List[Contact] = await self.repo.get_all_contacts(
            user_id, skip=pagination["skip"], limit=pagination["limit"], **filters
        )

        return contacts, total_count

    async def get_contacts_count(self, user_id: int) -> int:
        """Return the total number of contacts for a user."""
        return await self.repo.get_contacts_total_count(user_id)

    async def get_contacts_upcoming_birthdays(
        self, user_id: int, pagination: Dict[str, int]
    ) -> Tuple[List[Dict], int]:
        """Return a paginated list of contacts with upcoming birthdays."""
        return await self.repo.get_contacts_upcoming_birthdays(
            user_id, pagination["skip"], pagination["limit"]
        )

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
        return await self.repo.remove_contact_by_id(user_id, contact_id)
