"""
Contacts API endpoints.

Provides CRUD operations for notes, including listing, retrieving, creating,
updating, and deleting contacts.
"""

from typing import List, Optional

from fastapi import APIRouter, Query, Path, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas.contacts import (
    ContactModelSchema,
    ContactResponseSchema,
    ContactPartialUpdateSchema,
    ContactCelebrationResponseSchema,
)
from src.schemas.errors import ContactNotFoundErrorResponse

from src.database.models import Contact
import src.repository.contacts as repository_contacts

from src.utils.errors import raise_http_404_error


router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post(
    "/",
    response_model=ContactResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact",
    description="All fields except `info` are required.",
)
async def create_note(body: ContactModelSchema, db: AsyncSession = Depends(get_db)):
    """Create a new contact."""
    return await repository_contacts.create_contact(body, db)


@router.get(
    "/",
    response_model=List[ContactResponseSchema],
    summary="List all contacts",
    description=(
        "Retrieve a paginated list of contacts.\n\n"
        "Optional query parameters `first_name`, `last_name`, and `email` "
        "perform **case-insensitive partial matches** "
        "(e.g. `first_name=ann` matches `Annette`).\n\n"
        "`skip`  and `limit` control pagination and always apply, "
        "whether or not filters are provided."
    ),
)
async def read_all_contacts(
    first_name: Optional[str] = Query(
        None,
        description=(
            "Filer by first name match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    ),
    last_name: Optional[str] = Query(
        None,
        description=(
            "Filter by last name match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    ),
    email: Optional[str] = Query(
        None,
        description=(
            "Filter by e-mail match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip for pagination.",
        example=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of contacts to return.",
        example=50,
    ),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a paginated list of monitored resources."""
    contacts: List[Contact] = await repository_contacts.get_all_contacts(
        skip, limit, db, first_name, last_name, email
    )
    return contacts


@router.get(
    "/upcoming-birthdays",
    response_model=List[ContactCelebrationResponseSchema],
    summary="List all upcoming birthdays celebrations in 7 days",
    description=(
        "Retrieve all contacts whose birthdays fall within the next **7 days, inclusive** "
        "(_today_ through _today + 7 days_).\n\n"
        "The returned contact `celebration_date` field may differ from the actual birthdate:\n\n"
        "  - **Weekday birthdays (Mon-Fri):** **celebration_date** equals the birthdate.\n"
        "  - **Weekend birthdays (Sat-Sun):** celebration is **moved to the following Monday**.\n\n"
        "  - ⚠️ **Important**: Contacts whose birthdays fall on the weekend will be included "
        "**even if the shifted **celebration_date** lies beyond the strict 7-day range**.\n\n"
        "`info` field kept in reply as it may contain important personal preferences "
        "or limitations information."
    ),
)
async def get_upcoming_birthdays(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip for pagination.",
        example=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of contacts to return.",
        example=50,
    ),
    db: AsyncSession = Depends(get_db),
):
    """Return a list of contacts whose birthdays fall within the next 7 days."""
    return await repository_contacts.get_contacts_upcoming_birthdays(skip, limit, db)


@router.get(
    "/{contact_id}",
    response_model=ContactResponseSchema,
    summary="Get contact by ID",
    description="Retrieve a single contact by its unique identifier.",
    responses={
        404: {
            "model": ContactNotFoundErrorResponse,
            "description": "Contact not found",
        }
    },
)
async def read_single_contact_by_id(
    contact_id: int = Path(
        description="The ID of the contact to retrieve.",
        ge=1,
        example=1,
    ),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single contact by its ID."""
    contact = await repository_contacts.get_contact_by_id(contact_id, db)
    if contact is None:
        raise_http_404_error("Contact not found")
    return contact


@router.put(
    "/{contact_id}",
    response_model=ContactResponseSchema,
    summary="Update contact by ID (entirely)",
    description=(
        "Fully update an existing contact by its unique identifier. "
        "Requires all contact fields. Overwrites all fields."
    ),
    responses={
        404: {
            "model": ContactNotFoundErrorResponse,
            "description": "Contact not found",
        }
    },
)
async def overwrite_contact(
    body: ContactModelSchema,
    contact_id: int = Path(
        description="The ID of the contact to update.", ge=1, example=1
    ),
    db: AsyncSession = Depends(get_db),
):
    """Fully update an existing contact by ID."""
    note = await repository_contacts.update_contact_by_id(contact_id, body, db)
    if note is None:
        raise_http_404_error("Contact not found")
    return note


@router.patch(
    "/{contact_id}",
    response_model=ContactResponseSchema,
    summary="Update contact (partially)",
    description="Update only some provided fields of an existing contact. All fields are optional.",
    responses={
        404: {
            "model": ContactNotFoundErrorResponse,
            "description": "Contact not found",
        }
    },
)
async def update_contact(
    body: ContactPartialUpdateSchema,
    contact_id: int = Path(
        description="The ID of the contact to update.", ge=1, example=1
    ),
    db: AsyncSession = Depends(get_db),
):
    """Partially update an existing contact."""
    note = await repository_contacts.update_contact_by_id(contact_id, body, db)
    if note is None:
        raise_http_404_error("Contact not found")
    return note


@router.delete(
    "/{contact_id}",
    response_model=ContactResponseSchema,
    summary="Delete contact",
    description="Delete a contact by its ID and return the deleted object.",
    responses={
        404: {
            "model": ContactNotFoundErrorResponse,
            "description": "Contact not found",
        }
    },
)
async def delete_contact(
    contact_id: int = Path(
        description="The ID of the contact to delete.", ge=1, example=1
    ),
    db: AsyncSession = Depends(get_db),
):
    """Delete a contact by ID and return the deleted object."""
    contact = await repository_contacts.remove_contact(contact_id, db)
    if contact is None:
        raise_http_404_error("Contact not found")
    return contact
