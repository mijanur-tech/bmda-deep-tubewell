# ============================================================
# SECTION 1: IMPORTS
# Import Python date and datetime types.
# ============================================================

from datetime import date, datetime


# ============================================================
# SECTION 2: READING DATE VALIDATION
# Reading date rules:
#
# - must be a Python date
# - datetime values are rejected
# - future dates are not allowed
# - today is allowed
# - historical dates are allowed
# ============================================================

def validate_reading_date(
    reading_date: date,
    today: date | None = None,
) -> bool:

    if not isinstance(
        reading_date,
        date,
    ):
        return False

    if isinstance(
        reading_date,
        datetime,
    ):
        return False

    if today is None:
        today = date.today()

    if not isinstance(
        today,
        date,
    ):
        return False

    if isinstance(
        today,
        datetime,
    ):
        return False

    if reading_date > today:
        return False

    return True