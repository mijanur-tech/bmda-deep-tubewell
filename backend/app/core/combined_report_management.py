# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date

from sqlalchemy.orm import Session

from app.core.energy_report_management import (
    get_energy_report,
)

from app.core.prepaid_report_management import (
    get_prepaid_report,
)

from app.models.user import User


# ============================================================
# SECTION 2: COMBINED REPORT
#
# Role scope is enforced inside the Energy and Prepaid
# report cores. The same authenticated user is passed to both.
# ============================================================

def get_combined_report(
    db: Session,
    *,
    current_user: User,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise ValueError(
            "Start date cannot be after end date."
        )

    energy_report = get_energy_report(
        db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )

    prepaid_report = get_prepaid_report(
        db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "report_type":
            "combined",

        "energy":
            energy_report,

        "prepaid":
            prepaid_report,
    }