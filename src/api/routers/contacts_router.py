"""
Contacts API endpoints.

Provides operations for contacts, including listing, retrieving, creating,
updating, and deleting contacts.
"""

from fastapi import APIRouter, Path, Depends, status

from src.services import ContactService
from src.services.dtos import UserDTO
from src.services.errors import BadProvidedDataError
from src.utils.constants import MESSAGE_ERROR_CONTACT_NOT_FOUND
from src.utils.logger import logger

from src.api.dependencies import (
    get_current_active_user,
    get_contacts_service,
)
from src.api.errors import raise_http_400_error, raise_http_404_error
from src.api.responses.error_responses import (
    ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES,
    ON_UPDATE_EMPTY_BAD_REQUEST_RESPONSE,
    ON_CONTACT_NOT_FOUND_RESPONSE,
)
from src.api.schemas.contacts.requests import (
    ContactRequestSchema,
    ContactOptionalRequestSchema,
    ContactsFilterRequestSchema,
)
from src.api.schemas.contacts.responses import (
    ContactResponseSchema,
    ContactCelebrationResponseSchema,
)
from src.api.schemas.pagination import (
    PaginationFilterRequestSchema,
    PaginatedGenericResponseSchema,
)

router = APIRouter(
    prefix="/contacts",
    tags=["Contacts (User Access)"],
    responses={**ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES},
)


@router.post(
    "/",
    summary="Create a new contact",
    description="All fields except `info` are required.",
    response_model=ContactResponseSchema,
    status_code=status.HTTP_201_CREATED,
    response_description="Successfully created a new contact.",
)
async def create_contact(
    body: ContactRequestSchema,
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Create a new contact."""
    try:
        contact = await contacts_service.create_contact(user.id, **body.model_dump())
    except BadProvidedDataError as exc:
        logger.debug(exc)
        raise_http_400_error(detail=exc.errors)
    return ContactResponseSchema.model_validate(contact)


@router.get(
    "/",
    summary="List all contacts",
    description=(
        "Retrieve a paginated list of contacts.\n\n"
        "Optional query parameters `first_name`, `last_name`, and `email` "
        "perform **case-insensitive partial matches** "
        "(e.g. `first_name=ann` matches `Annette`).\n\n"
        "`skip`  and `limit` control pagination and always apply, "
        "whether or not filters are provided."
    ),
    response_model=PaginatedGenericResponseSchema[ContactResponseSchema],
    status_code=status.HTTP_200_OK,
    response_description="Successfully retrieved all user contacts.",
)
async def get_all_contacts(
    pagination: PaginationFilterRequestSchema = Depends(),
    filters: ContactsFilterRequestSchema = Depends(),
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> PaginatedGenericResponseSchema[ContactResponseSchema]:
    """Retrieve a paginated list of contacts with optional filtration."""

    contacts, total_count = await contacts_service.get_all_contacts(
        user.id, pagination.model_dump(), filters.model_dump()
    )

    return PaginatedGenericResponseSchema.model_validate(
        {
            "total": total_count,
            "skip": pagination.skip,
            "limit": pagination.limit,
            "data": [ContactResponseSchema.model_validate(c) for c in contacts],
        }
    )


@router.get(
    "/upcoming-birthdays",
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
    response_model=PaginatedGenericResponseSchema[ContactCelebrationResponseSchema],
    status_code=status.HTTP_200_OK,
    response_description="Successfully retrieved all user contacts upcoming birthdays.",
)
async def get_upcoming_birthdays(
    pagination: PaginationFilterRequestSchema = Depends(),
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> PaginatedGenericResponseSchema[ContactCelebrationResponseSchema]:
    """Return a paginated list of contacts whose birthdays fall within the next 7 days."""
    birthdays, total_count = await contacts_service.get_contacts_upcoming_birthdays(
        user.id, pagination.model_dump()
    )
    return PaginatedGenericResponseSchema.model_validate(
        {
            "total": total_count,
            "skip": pagination.skip,
            "limit": pagination.limit,
            "data": [
                ContactCelebrationResponseSchema.model_validate(b) for b in birthdays
            ],
        }
    )


@router.get(
    "/{contact_id}",
    summary="Get contact by ID",
    description="Retrieve a single contact by its unique identifier.",
    response_model=ContactResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully retrieved user contact.",
    responses={**ON_CONTACT_NOT_FOUND_RESPONSE},
)
async def get_single_contact_by_id(
    contact_id: int = Path(
        description="The ID of the contact to retrieve.",
        ge=1,
        example=1,
    ),
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Retrieve a single contact by its ID."""
    contact = await contacts_service.get_contact_by_id(user.id, contact_id)
    if contact is None:
        raise_http_404_error(MESSAGE_ERROR_CONTACT_NOT_FOUND)
    return ContactResponseSchema.model_validate(contact)


@router.put(
    "/{contact_id}",
    summary="Update contact by ID (update entirely by overwriting)",
    description=(
        "Fully update an existing contact by its unique identifier.\n\n"
        "Requires all contact fields. Overwrites all fields.\n\n<br>"
        "*Note*: for partial contact update, please user ***PUT*** method."
    ),
    response_model=ContactResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully updated user contact.",
    responses={**ON_CONTACT_NOT_FOUND_RESPONSE},
)
async def overwrite_contact(
    body: ContactRequestSchema,
    contact_id: int = Path(
        description="The ID of the contact to update.", ge=1, example=1
    ),
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Fully update an existing contact by ID."""
    try:
        contact = await contacts_service.overwrite_contact_by_id(
            user.id, contact_id, **body.model_dump()
        )
    except BadProvidedDataError as exc:
        logger.debug(exc)
        raise_http_400_error(detail=exc.errors)

    if contact is None:
        raise_http_404_error(MESSAGE_ERROR_CONTACT_NOT_FOUND)

    return ContactResponseSchema.model_validate(contact)


@router.patch(
    "/{contact_id}",
    summary="Update contact by ID (update partially)",
    description=(
        "Update only some provided fields of an existing contact.\n\n<br>"
        "All fields are optional, but at least one field should be provided."
    ),
    response_model=ContactResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully updated user contact.",
    responses={**ON_UPDATE_EMPTY_BAD_REQUEST_RESPONSE, **ON_CONTACT_NOT_FOUND_RESPONSE},
)
async def patch_contact(
    body: ContactOptionalRequestSchema,
    contact_id: int = Path(
        description="The ID of the contact to update.", ge=1, example=1
    ),
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Partially update an existing contact."""
    try:
        contact = await contacts_service.update_contact_partially(
            user.id, contact_id, **body.model_dump(exclude_unset=True)
        )
    except BadProvidedDataError as exc:
        logger.debug(exc)
        raise_http_400_error(detail=exc.errors)

    if contact is None:
        raise_http_404_error(MESSAGE_ERROR_CONTACT_NOT_FOUND)

    return ContactResponseSchema.model_validate(contact)


@router.delete(
    "/{contact_id}",
    summary="Delete contact",
    description="Delete a contact by its ID and return the deleted object.",
    response_model=ContactResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully deleted user contact.",
    responses={**ON_CONTACT_NOT_FOUND_RESPONSE},
)
async def delete_contact(
    contact_id: int = Path(
        description="The ID of the contact to delete.", ge=1, example=1
    ),
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> ContactResponseSchema:
    """Delete a contact by ID and return the deleted object."""
    contact = await contacts_service.remove_contact(user.id, contact_id)
    if contact is None:
        raise_http_404_error(MESSAGE_ERROR_CONTACT_NOT_FOUND)
    return ContactResponseSchema.model_validate(contact)
