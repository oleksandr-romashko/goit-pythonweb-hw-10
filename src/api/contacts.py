"""
Contacts API endpoints.

Provides CRUD operations for contacts, including listing, retrieving, creating,
updating, and deleting contacts.
"""

from typing import List

from fastapi import APIRouter, Path, Depends, status

from src.schemas.contacts import (
    ContactModelSchema,
    ContactResponseSchema,
    ContactPartialUpdateSchema,
    ContactCelebrationResponseSchema,
    ContactsFilterSchema,
    get_contacts_query_filter,
)
from src.schemas.pagination import PaginationFilterSchema, get_pagination_filter
from src.schemas.errors import ContactNotFoundErrorResponse
from src.services.contacts_service import get_contacts_service, ContactsService

from src.utils.errors import raise_http_404_error


router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post(
    "/",
    response_model=ContactResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact",
    description="All fields except `info` are required.",
)
async def create_contact(
    body: ContactModelSchema,
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Create a new contact."""
    return await contacts_service.create_contact(body)


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
async def get_all_contacts(
    pagination: PaginationFilterSchema = Depends(get_pagination_filter),
    filters: ContactsFilterSchema = Depends(get_contacts_query_filter),
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> List[ContactResponseSchema]:
    """Retrieve a paginated list of contacts with optional filters."""
    return await contacts_service.get_all_contacts(pagination, filters)


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
    pagination: PaginationFilterSchema = Depends(get_pagination_filter),
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> List[ContactCelebrationResponseSchema]:
    """Return a list of contacts whose birthdays fall within the next 7 days."""
    return await contacts_service.get_contacts_upcoming_birthdays(pagination)


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
async def get_single_contact_by_id(
    contact_id: int = Path(
        description="The ID of the contact to retrieve.",
        ge=1,
        example=1,
    ),
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Retrieve a single contact by its ID."""
    contact = await contacts_service.get_contact_by_id(contact_id)
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
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Fully update an existing contact by ID."""
    contact = await contacts_service.update_contact_by_id(contact_id, body)
    if contact is None:
        raise_http_404_error("Contact not found")
    return contact


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
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Partially update an existing contact."""
    contact = await contacts_service.update_contact_by_id(contact_id, body)
    if contact is None:
        raise_http_404_error("Contact not found")
    return contact


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
    contacts_service: ContactsService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Delete a contact by ID and return the deleted object."""
    contact = await contacts_service.remove_contact(contact_id)
    if contact is None:
        raise_http_404_error("Contact not found")
    return contact
