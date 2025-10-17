"""
Repository layer for Contact entities.

Provides asynchronous CRUD operations and query helpers.

This layer encapsulates all database logic, isolating it from business and routing layers.
"""

from datetime import date, timedelta
from typing import Optional, Any, List, Dict, Tuple

from sqlalchemy import select, func, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import app_config
from src.db.models import Contact
from src.utils.date_helpers import calc_celebration_date
from src.utils.orm_helpers import orm_to_dict


class ContactsRepository:
    """Provides low-level asynchronous database operations for Contact entities."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_contact(self, user_id: int, data: Dict[str, Any]) -> Contact:
        """Create a new contact."""
        contact = Contact(user_id=user_id, **data)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_contacts_total_count(self, user_id: int) -> int:
        """Return the total number of contacts for a user."""
        result = await self.db.execute(
            select(func.count()).filter(  # pylint: disable=E1102
                Contact.user_id == user_id
            )
        )
        return result.scalar() or 0

    async def get_all_contacts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Contact]:
        """Return a paginated list of contacts filtered by optional fields."""
        stmt = select(Contact).filter(Contact.user_id == user_id)

        # Optional filters
        if first_name:
            stmt = stmt.where(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.where(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.where(Contact.email.ilike(f"%{email}%"))

        stmt = (
            stmt.order_by(
                func.lower(Contact.first_name),
                func.lower(Contact.last_name),
                Contact.birthdate,
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_contacts_upcoming_birthdays(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        today: Optional[date] = None,
        upcoming_days: Optional[int] = None,
        move_feb29_to_feb_28: Optional[bool] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Return a paginated list of contacts with upcoming birthdays.

        Adds `celebration_date` field to the respond object, that
        - equals birthdate if it's a weekday (Monday - Friday)
        - next Monday if it falls on a weekend (Saturday, Sunday)
        """

        upcoming_period_days = (
            upcoming_days or app_config.UPCOMING_BIRTHDAYS_PERIOD_DAYS
        )
        move_feb29_to_feb28 = (
            move_feb29_to_feb_28 or app_config.DO_MOVE_CELEBRATION_FEB_29_TO_FEB_28
        )

        # Define upcoming dates range
        start_date = today if today is not None else date.today()
        end_date = start_date + timedelta(days=upcoming_period_days)

        # Get all contacts within the upcoming date range
        base_query = select(
            Contact, func.count().over().label("total_count")  # pylint: disable=E1102
        ).filter(Contact.user_id == user_id)

        if end_date.month == start_date.month:
            # same month birthdays
            base_query = base_query.filter(
                extract("month", Contact.birthdate) == start_date.month,
                extract("day", Contact.birthdate).between(start_date.day, end_date.day),
            )
        else:
            # birthdays wrap to the next month
            base_query = base_query.filter(
                or_(
                    # remainder of current month
                    (extract("month", Contact.birthdate) == start_date.month)
                    & (extract("day", Contact.birthdate) >= start_date.day),
                    # beginning of the next month
                    (extract("month", Contact.birthdate) == end_date.month)
                    & (extract("day", Contact.birthdate) <= end_date.day),
                )
            )

        # Apply ordering and pagination
        stmt = (
            base_query.order_by(
                Contact.birthdate,
                func.lower(Contact.first_name),
                func.lower(Contact.last_name),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return [], 0

        total_count = rows[0].total_count
        contacts = [row.Contact for row in rows]

        # Add celebration date to each contact
        contacts_with_celebration = []
        current_year = start_date.year
        for contact in contacts:
            # calculate celebration date
            celebration_date = calc_celebration_date(
                contact.birthdate, current_year, move_feb29_to_feb28
            )
            # combine contact with celebration date
            contact_dict = orm_to_dict(contact)
            contact_dict["celebration_date"] = celebration_date
            contacts_with_celebration.append(contact_dict)

        # Sort by celebration_date
        contacts_with_celebration.sort(
            key=lambda c: (
                c["celebration_date"],
                c["birthdate"],
                c["first_name"].lower(),
                c["last_name"].lower(),
            )
        )

        return contacts_with_celebration, total_count

    async def get_contact_by_id(
        self, user_id: int, contact_id: int
    ) -> Optional[Contact]:
        """Return a single contact by ID, or None if not found."""
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_contact_by_id(
        self,
        user_id: int,
        contact_id: int,
        fields: Dict[str, Any],
    ) -> Optional[Contact]:
        """Update a contact, or return None if not found."""
        contact = await self.get_contact_by_id(user_id, contact_id)

        if contact is None:
            return None

        for key, value in fields.items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def remove_contact_by_id(
        self, user_id: int, contact_id: int
    ) -> Optional[Contact]:
        """Remove a contact by ID, or return None if not found."""
        contact = await self.get_contact_by_id(user_id, contact_id)

        if contact is None:
            return None

        await self.db.delete(contact)
        await self.db.commit()
        return contact
