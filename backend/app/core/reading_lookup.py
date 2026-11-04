# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.reading_management import (
    validate_reading_submission_access,
)

from app.models.reading import Reading


# ============================================================
# SECTION 2: LATEST READING LOOKUP
#
# The current Field User must be authorized for the tubewell.
#
# IMPORTANT:
# The previous reading belongs to the tubewell/meter history,
# not only to the Field User who submitted it.
#
# This allows reading continuity after Field User reassignment.
# ============================================================

def get_latest_reading_for_field_user(
    db: Session,
    *,
    tubewell_id: int,
    field_user_id: int,
    reading_type: str,
    meter_id: int | None = None,
) -> Reading | None:

    # --------------------------------------------------------
    # Only the currently assigned Field User may request
    # previous reading data for this tubewell.
    # --------------------------------------------------------

    if not validate_reading_submission_access(
        db,
        tubewell_id,
        field_user_id,
    ):
        raise ValueError(
            "Field User is not authorized to access "
            "reading history for this tubewell."
        )

    # --------------------------------------------------------
    # Reading type must be one of the supported final types.
    # --------------------------------------------------------

    if reading_type not in (
        "energy",
        "prepaid",
    ):
        raise ValueError(
            "Unsupported reading type."
        )

    # --------------------------------------------------------
    # Search the tubewell's reading history.
    #
    # Notice:
    # There is intentionally NO collected_by_user_id filter.
    # --------------------------------------------------------

    query = select(Reading).where(
        Reading.tubewell_id == tubewell_id,
        Reading.reading_type == reading_type,
    )

    # --------------------------------------------------------
    # When a meter is supplied, keep previous reading history
    # tied to that exact meter.
    # --------------------------------------------------------

    if meter_id is not None:
        query = query.where(
            Reading.meter_id == meter_id
        )

    # --------------------------------------------------------
    # Latest reading:
    # newest reading date first,
    # then newest database ID.
    # --------------------------------------------------------

    query = query.order_by(
        Reading.reading_date.desc(),
        Reading.id.desc(),
    )

    return db.scalar(
        query.limit(1)
    )