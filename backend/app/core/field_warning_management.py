# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.reading_warning_management import (
    get_missing_reading_warning,
)

from app.models.tubewell import Tubewell

from app.models.tubewell_assignment import (
    TubewellAssignment,
)


# ============================================================
# SECTION 2: GET CURRENT ASSIGNED TUBEWELLS
# ============================================================

def get_current_assigned_tubewell_ids(
    db: Session,
    *,
    field_user_id: int,
) -> list[int]:

    if (
        not isinstance(field_user_id, int)
        or isinstance(field_user_id, bool)
        or field_user_id <= 0
    ):
        raise ValueError(
            "Invalid Field User ID."
        )

    query = (
        select(
            TubewellAssignment.tubewell_id
        )
        .where(
            TubewellAssignment.field_user_id
            == field_user_id,

            TubewellAssignment.ended_at
            .is_(None),
        )
        .order_by(
            TubewellAssignment.tubewell_id
        )
    )

    return list(
        db.scalars(
            query
        ).all()
    )


# ============================================================
# SECTION 3: BUILD INACTIVE TUBEWELL WARNING
#
# IMPORTANT:
# Inactive tubewells are still allowed to receive readings.
# This warning is informational only.
# ============================================================

def get_inactive_tubewell_warning(
    db: Session,
    *,
    tubewell_id: int,
) -> dict | None:

    tubewell = db.get(
        Tubewell,
        tubewell_id,
    )

    if tubewell is None:
        return None

    if tubewell.is_active:
        return None

    return {
        "tubewell_id":
            tubewell.id,

        "meter_id":
            None,

        "warning_type":
            "inactive_tubewell",

        "reading_type":
            None,

        "warning":
            True,

        "days_since_last_reading":
            None,

        "latest_reading_date":
            None,

        "message":
            (
                "Tubewell is inactive. "
                "Reading submission is still allowed."
            ),
    }


# ============================================================
# SECTION 4: BUILD WARNINGS FOR FIELD USER
#
# Each assigned tubewell may return:
# - Energy missing-reading status
# - Prepaid missing-reading status
# - Inactive tubewell warning
# ============================================================

def get_field_user_missing_reading_warnings(
    db: Session,
    *,
    field_user_id: int,
) -> list[dict]:

    tubewell_ids = (
        get_current_assigned_tubewell_ids(
            db,
            field_user_id=field_user_id,
        )
    )

    warnings = []

    for tubewell_id in tubewell_ids:

        energy_warning = (
            get_missing_reading_warning(
                db,
                tubewell_id=tubewell_id,
                reading_type="energy",
            )
        )

        prepaid_warning = (
            get_missing_reading_warning(
                db,
                tubewell_id=tubewell_id,
                reading_type="prepaid",
            )
        )

        # ----------------------------------------------------
        # Add explicit warning type to existing warning output.
        # ----------------------------------------------------

        energy_warning[
            "warning_type"
        ] = "missing_reading"

        prepaid_warning[
            "warning_type"
        ] = "missing_reading"

        warnings.append(
            energy_warning
        )

        warnings.append(
            prepaid_warning
        )

        # ----------------------------------------------------
        # Add informational inactive-tubewell warning.
        # ----------------------------------------------------

        inactive_warning = (
            get_inactive_tubewell_warning(
                db,
                tubewell_id=tubewell_id,
            )
        )

        if inactive_warning is not None:
            warnings.append(
                inactive_warning
            )

    return warnings