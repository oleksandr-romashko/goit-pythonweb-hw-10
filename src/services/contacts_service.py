"""Service layer for Contact entities."""

from typing import List, Optional, Union, Dict

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db_session
from src.database.models.contact import Contact
from src.repository.contacts_repository import ContactsRepository
from src.schemas.contacts import (
    ContactCelebrationResponseSchema,
    ContactsFilterSchema,
    ContactModelSchema,
    ContactPartialUpdateSchema,
    ContactResponseSchema,
)
from src.schemas.pagination import PaginationFilterSchema


class ContactsService:
    """Handles business logic for contacts."""

    def __init__(self, db_session: AsyncSession):
        """Initialize service with a database session."""
        self.repo = ContactsRepository(db_session)

    async def create_contact(self, body: ContactModelSchema) -> ContactResponseSchema:
        """Create a new contact."""
        contact: Contact = await self.repo.create_contact(body.model_dump())
        return ContactResponseSchema.model_validate(contact)

    async def get_all_contacts(
        self, pagination: PaginationFilterSchema, filters: ContactsFilterSchema
    ) -> List[ContactResponseSchema]:
        """Return a paginated list of contacts with optional filters."""
        contacts: List[Contact] = await self.repo.get_all_contacts(
            skip=pagination.skip, limit=pagination.limit, **filters.model_dump()
        )
        return [ContactResponseSchema.model_validate(x) for x in contacts]

    async def get_contacts_upcoming_birthdays(
        self, pagination: PaginationFilterSchema
    ) -> List[ContactCelebrationResponseSchema]:
        """Return contacts with upcoming birthdays."""
        skip = pagination.skip
        limit = pagination.limit
        birthdays: List[Dict] = await self.repo.get_contacts_upcoming_birthdays(
            skip, limit
        )
        return [ContactCelebrationResponseSchema.model_validate(x) for x in birthdays]

    async def get_contact_by_id(
        self, contact_id: int
    ) -> Optional[ContactResponseSchema]:
        """Retrieve a contact by its ID or None if not exists."""
        contact: Optional[Contact] = await self.repo.get_contact_by_id(contact_id)
        return ContactResponseSchema.model_validate(contact) if contact else None

    async def update_contact_by_id(
        self,
        contact_id: int,
        body: Union[ContactModelSchema, ContactPartialUpdateSchema],
    ) -> Optional[ContactResponseSchema]:
        """Update a contact fully or partially."""
        contact: Optional[Contact] = await self.repo.update_contact_by_id(
            contact_id, body.model_dump(exclude_unset=True)
        )
        return ContactResponseSchema.model_validate(contact) if contact else None

    async def remove_contact(self, contact_id: int) -> Optional[ContactResponseSchema]:
        """Delete a contact by its ID."""
        contact: Optional[Contact] = await self.repo.remove_contact(contact_id)
        return ContactResponseSchema.model_validate(contact) if contact else None


def get_contacts_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> ContactsService:
    """Dependency provider for ContactsService."""
    return ContactsService(db_session)
