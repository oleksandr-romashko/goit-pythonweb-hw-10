"""Helper functions for date-related operations."""

import calendar
from datetime import date, timedelta


def calc_celebration_date(
    birthdate: date, cur_year: int, move_feb29_to_feb28: bool
) -> date:
    """
    Calculate the actual celebration date for a birthday.

    Rules:
    - If birthday falls on a weekend (Saturday or Sunday), move to next Monday.
    - For Feb 29 birthdays in non-leap years, move to Feb 28 or Mar 1 depending on flag.

    Args:
        birthdate (date): Original birthdate.
        cur_year (int): Year to calculate celebration date for.
        move_feb29_to_feb28 (bool): If True, Feb 29 birthdays move to Feb 28 in non-leap years.

    Returns:
        date: Celebration date for the given year.
    """
    # Define birthday this year
    if (birthdate.month, birthdate.day) == (2, 29) and not calendar.isleap(cur_year):
        # handle Feb 29
        bd = date(cur_year, 2, 28) if move_feb29_to_feb28 else date(cur_year, 3, 1)
    else:
        bd = birthdate.replace(year=cur_year)

    # Move weekend birthdays to next Monday
    celebration_date = bd
    if bd.weekday() in (5, 6):  # Sat=5, Sun=6
        # move to next Monday
        celebration_date += timedelta(days=7 - bd.weekday())

    return celebration_date
