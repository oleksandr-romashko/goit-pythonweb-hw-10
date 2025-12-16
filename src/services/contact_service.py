"""Service layer providing business logic for managing Contact entities."""

from typing import Optional, Any, List, Dict, Tuple
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contact
from src.db.repository import ContactsRepository
from src.providers.cache_provider.contacts_count_cache import (
    ContactsCountUserRedisCacheProvider,
)
from src.utils.constants import LOG_CONTACT_TEMPLATE
from src.utils.logger import logger
from src.utils.query_helpers import get_pagination

from .errors import BadProvidedDataError


class ContactService:
    """
    Handles business logic related to contacts.

    ContactService caching policy:
    - Contacts count cache is keyed based on user_id
    - Cache is invalidated on all write paths that affect count
    - Read paths may warm the cache
    """

    @staticmethod
    def _validate_at_least_has_one_name_field(
        first_name: Optional[str],
        last_name: Optional[str],
    ) -> None:
        """
        Check at least one of name fields has actual value

        Raises:
            BadProvidedDataError: If both values have no value.
        """
        if not first_name and not last_name:
            raise BadProvidedDataError(
                {"name": "At least first_name or last_name must be provided"}
            )

    @staticmethod
    def _validate_birthday_not_in_the_future(birthdate: date) -> None:
        """
        Check birthday is not in the future

        Raises:
            BadProvidedDataError: If birthday is in the future."""
        if birthdate > date.today():
            raise BadProvidedDataError(
                {"birthdate": "Birthdate cannot be in the future"}
            )

    @staticmethod
    def _normalize_full_data(
        first_name: Optional[str],
        last_name: Optional[str],
        email: str,
        phone_number: str,
        birthdate: date,
        info: Optional[str],
    ) -> Dict[str, Any]:
        """Normalize partial data and returns dict out of normalized data"""
        return {
            "first_name": (first_name or "").strip(),
            "last_name": (last_name or "").strip(),
            "email": email.strip(),
            "phone_number": phone_number.strip(),
            "birthdate": birthdate,
            "info": (info or "").strip(),
        }

    @staticmethod
    def _normalize_partial_data(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        birthdate: Optional[date] = None,
        info: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize partial data and returns dict out of normalized data"""
        update_data: Dict[str, Any] = {}

        if first_name is not None:
            first_name_normalized = first_name.strip()
            update_data["first_name"] = first_name_normalized

        if last_name is not None:
            last_name_normalized = last_name.strip()
            update_data["last_name"] = last_name_normalized

        if email is not None:
            update_data["email"] = email.strip()

        if phone_number is not None:
            update_data["phone_number"] = phone_number.strip()

        if birthdate is not None:
            update_data["birthdate"] = birthdate

        if info is not None:
            update_data["info"] = info.strip()

        return update_data

    def __init__(
        self,
        db_session: AsyncSession,
        *,
        repo: Optional[ContactsRepository] = None,
        contacts_count_cache: Optional[ContactsCountUserRedisCacheProvider] = None,
    ):
        """Initialize the service with a contacts repository."""
        self.repo: ContactsRepository = repo or ContactsRepository(db_session)
        self.contacts_count_cache: Optional[ContactsCountUserRedisCacheProvider] = (
            contacts_count_cache
        )

    async def create_contact(
        self,
        user_id: int,
        first_name: Optional[str],
        last_name: Optional[str],
        email: str,
        phone_number: str,
        birthdate: date,
        info: Optional[str],
    ) -> Contact:
        """
        Create a new contact for a given user.

        Invalidates contacts count cache, if cache is available.

        Raises:
            BadProvidedDataError:
            - If both name fields values have no value.
            - If birthday is in the future
        """

        # Domain checks
        ContactService._validate_at_least_has_one_name_field(first_name, last_name)
        ContactService._validate_birthday_not_in_the_future(birthdate)

        # Normalize
        normalized_data = ContactService._normalize_full_data(
            first_name, last_name, email, phone_number, birthdate, info
        )

        # Call repository to create
        contact = await self.repo.create_contact(user_id, normalized_data)
        logger.debug(LOG_CONTACT_TEMPLATE, "CONTACT_CREATED", user_id, contact.id)

        # Invalidate user contacts count cache
        if self.contacts_count_cache:
            await self.contacts_count_cache.invalidate_contacts_count(user_id)

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
        """
        Return the total number of contacts for a user.

        Provided with contacts count caching (read/write), if cache is available.
        """
        # 1. Try get user from cache
        if self.contacts_count_cache:
            contacts_count_cached: Optional[int] = (
                await self.contacts_count_cache.get_contacts_count(user_id)
            )
            if contacts_count_cached is not None:
                logger.debug(
                    "[CACHE HIT] User contacts count for user_id=%s",
                    user_id,
                )
                return contacts_count_cached
            logger.debug("[CACHE MISS] User contacts count for user_id=%s", user_id)
        else:
            logger.debug("[CACHE SKIPPED] User contacts count cache is disabled")

        # 2. If not in cache --> request from DB
        contacts_count = await self.repo.get_contacts_total_count(user_id)

        # 3. Save to cache
        if self.contacts_count_cache:
            await self.contacts_count_cache.set_contacts_count(user_id, contacts_count)

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

    async def overwrite_contact_by_id(
        self,
        user_id: int,
        contact_id: int,
        first_name: Optional[str],
        last_name: Optional[str],
        email: str,
        phone_number: str,
        birthdate: date,
        info: Optional[str],
    ) -> Optional[Contact]:
        """
        Update a contact fully or partially.

        No need to invalidate contacts count cache, as ownership/count does not change

        Raises:
            BadProvidedDataError:
            - If both name fields values have no value.
            - If birthday is in the future
        """

        # Domain checks
        ContactService._validate_at_least_has_one_name_field(first_name, last_name)
        ContactService._validate_birthday_not_in_the_future(birthdate)

        # Normalize
        normalized_data = ContactService._normalize_full_data(
            first_name, last_name, email, phone_number, birthdate, info
        )

        # Call repository to update
        contact = await self.repo.update_contact_by_id(
            user_id, contact_id, normalized_data
        )
        if not contact:
            return None
        logger.debug(LOG_CONTACT_TEMPLATE, "CONTACT_UPDATED_FULL", user_id, contact.id)

        return contact

    async def update_contact_partially(
        self,
        user_id: int,
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        birthdate: Optional[date] = None,
        info: Optional[str] = None,
    ) -> Optional[Contact]:
        """
        Partially update an existing contact.

        Only fields that are provided will be updated.

        No need to invalidate contacts count cache, as ownership/count does not change

        Raises:
            BadProvidedDataError:
            - If no fields provided
            - If both name fields values have no value (checks against provided data and DB data).
            - If birthday is in the future
        """

        # Check that at least one field is provided
        if all(
            field is None
            for field in [first_name, last_name, email, phone_number, birthdate, info]
        ):
            raise BadProvidedDataError(
                {"fields": "At least one field must be provided for update"}
            )

        # Check birthday field not in the future
        if birthdate is not None:
            ContactService._validate_birthday_not_in_the_future(birthdate)

        # Normalize only provided fields
        update_data = ContactService._normalize_partial_data(
            first_name, last_name, email, phone_number, birthdate, info
        )

        # Check at least one of first_name and last_name is not empty (DB vs update fields)

        # Get contact from DB
        contact_db = await self.repo.get_contact_by_id(user_id, contact_id)
        if contact_db is None:
            return None

        # Check at least one name field has value
        new_first_name = (
            update_data["first_name"]
            if "first_name" in update_data
            else contact_db.first_name
        )
        new_last_name = (
            update_data["last_name"]
            if "last_name" in update_data
            else contact_db.last_name
        )
        if not new_first_name and not new_last_name:
            errors = {"name": "At least first_name or last_name must be provided"}
            if not new_first_name:
                errors["first_name"] = "first_name can't be empty"
            if not new_last_name:
                errors["last_name"] = "last_name can't be empty"
            raise BadProvidedDataError(errors)

        # Call repository to update
        contact = await self.repo.update_contact_by_id(user_id, contact_id, update_data)
        if not contact:
            return None
        logger.debug(
            LOG_CONTACT_TEMPLATE, "CONTACT_UPDATED_PARTIAL", user_id, contact.id
        )

        return contact

    async def remove_contact(self, user_id: int, contact_id: int) -> Optional[Contact]:
        """
        Delete a contact by ID.

        Invalidates contacts count cache, if cache is available.
        """
        contact = await self.repo.remove_contact_by_id(user_id, contact_id)
        if not contact:
            return None
        logger.debug(LOG_CONTACT_TEMPLATE, "CONTACT_DELETED", user_id, contact.id)

        # Delete user contacts count cache
        if self.contacts_count_cache:
            await self.contacts_count_cache.invalidate_contacts_count(user_id)

        return contact
