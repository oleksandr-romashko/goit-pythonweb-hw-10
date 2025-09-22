"""
Repository layer for Contact entities.

Provides asynchronous CRUD operations and helper queries for contacts,
including:

* Creating, reading, updating, and deleting contacts.
* Case-insensitive filtering and paginated listing.
* Retrieving contacts with upcoming birthdays (including leap-year handling
  and automatic adjustment of weekend birthdays to the following Monday).

This module isolates database logic (SQLAlchemy AsyncSession) from the
application's routing layer.
"""

from datetime import date, timedelta
from typing import Optional, Union, List, Dict
from sqlalchemy import select, func, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact
from src.schemas.contacts import (
    ContactModelSchema,
    ContactPartialUpdateSchema,
)

from src.config.app_config import config as app_config
from src.utils.date_helpers import calc_celebration_date
from src.utils.orm_helpers import contact_to_dict


async def create_contact(body: ContactModelSchema, db: AsyncSession) -> Contact:
    """Create a new contact."""
    contact = Contact(**body.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_all_contacts(
    skip: int,
    limit: int,
    db: AsyncSession,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
) -> List[Contact]:
    """Return a paginated list of contacts."""
    stmt = select(Contact)

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

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contacts_upcoming_birthdays(
    skip: int,
    limit: int,
    db: AsyncSession,
    today: date | None = None,
    upcoming_days: int | None = None,
    move_feb29_to_feb_28: bool | None = None,
) -> List[Dict]:
    """
    Return a paginated list of contacts with upcoming birthdays in 7 days.

    Adds `celebration_date` field to the respond object, that
    - equals birthdate if it's a weekday (Monday - Friday)
    - next Monday if it falls on a weekend (Saturday, Sunday)
    """
    upcoming_period_days = upcoming_days or app_config.UPCOMING_BIRTHDAYS_PERIOD_DAYS
    move_feb29_to_feb28 = (
        move_feb29_to_feb_28 or app_config.DO_MOVE_CELEBRATION_FEB_29_TO_FEB_28
    )

    # Define upcoming dates range
    start_date = today if today is not None else date.today()
    end_date = start_date + timedelta(days=upcoming_period_days)

    # Get all contacts that are in upcoming rage
    if end_date.month == start_date.month:
        # same month
        stmt = (
            select(Contact)
            .where(
                extract("month", Contact.birthdate) == start_date.month,
                extract("day", Contact.birthdate).between(start_date.day, end_date.day),
            )
            .order_by(
                Contact.birthdate,
                func.lower(Contact.first_name),
                func.lower(Contact.last_name),
            )
            .offset(skip)
            .limit(limit)
        )
    else:
        # wraps to next month
        stmt = select(Contact).where(
            or_(
                # remainder of current month
                (extract("month", Contact.birthdate) == start_date.month)
                & (extract("day", Contact.birthdate) >= start_date.day),
                # beginning of next month
                (extract("month", Contact.birthdate) == end_date.month)
                & (extract("day", Contact.birthdate) <= end_date.day),
            )
        )
    query_results = await db.execute(stmt)
    contacts = query_results.scalars().all()

    # Add celebration date to each contact
    contacts_with_celebration = []
    current_year = start_date.year
    for contact in contacts:
        # calculate celebration date
        celebration_date = calc_celebration_date(
            contact.birthdate, current_year, move_feb29_to_feb28
        )
        # combine contact with celebration date
        contact_dict = contact_to_dict(contact)
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

    return contacts_with_celebration


async def get_contact_by_id(contact_id: int, db: AsyncSession) -> Optional[Contact]:
    """Return a single note by ID, or None if not found."""
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_contact_by_id(
    contact_id: int,
    body: Union[ContactModelSchema, ContactPartialUpdateSchema],
    db: AsyncSession,
) -> Optional[Contact]:
    """Fully update a contact, or return None if not found."""
    contact = await get_contact_by_id(contact_id, db)

    if contact is None:
        return None

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)

    await db.commit()
    await db.refresh(contact)

    return contact


async def remove_contact(contact_id: int, db: AsyncSession) -> Optional[Contact]:
    """Remove a contact by ID, or return None if not found."""
    contact = await get_contact_by_id(contact_id, db)

    if contact is None:
        return None

    await db.delete(contact)
    await db.commit()
    return contact
