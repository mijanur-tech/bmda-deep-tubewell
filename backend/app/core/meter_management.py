# ============================================================
# SECTION 1: IMPORTS
# Import Python date type for meter date validation.
# ============================================================

from datetime import date, datetime


# ============================================================
# SECTION 2: METER DATE VALIDATION
# Check meter installation and removal dates.
#
# True  = Dates are valid.
# False = Dates are invalid.
#
# This function does not access or change the database.
# ============================================================

def validate_meter_dates(
    installed_at: date | None,
    removed_at: date | None,
) -> bool:

    # --------------------------------------------------------
    # CHECK 1: Installation date must be a date or None.
    # Reject datetime values to avoid mixing date and time.
    # --------------------------------------------------------

    if installed_at is not None:
        if not isinstance(installed_at, date):
            return False

        if isinstance(installed_at, datetime):
            return False

    # --------------------------------------------------------
    # CHECK 2: Removal date must be a date or None.
    # --------------------------------------------------------

    if removed_at is not None:
        if not isinstance(removed_at, date):
            return False

        if isinstance(removed_at, datetime):
            return False

    # --------------------------------------------------------
    # CHECK 3: Both dates can be unknown.
    # Do not invent missing dates.
    # --------------------------------------------------------

    if installed_at is None and removed_at is None:
        return True

    # --------------------------------------------------------
    # CHECK 4: Removal date requires installation date.
    # --------------------------------------------------------

    if installed_at is None and removed_at is not None:
        return False

    # --------------------------------------------------------
    # CHECK 5: Installation date without removal date
    # is acceptable.
    # --------------------------------------------------------

    if removed_at is None:
        return True

    # --------------------------------------------------------
    # CHECK 6: Removal cannot happen before installation.
    # Same-day replacement is allowed.
    # --------------------------------------------------------

    if removed_at < installed_at:
        return False

    # --------------------------------------------------------
    # RESULT: All validation checks passed.
    # --------------------------------------------------------

    return True