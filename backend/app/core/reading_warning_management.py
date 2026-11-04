# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reading import Reading


# ============================================================
# SECTION 2: WARNING THRESHOLD
# ============================================================

MISSING_READING_WARNING_DAYS = 30


# ============================================================
# SECTION 3: GET LATEST READING
# ============================================================

def get_latest_reading(
    db: Session,
    *,
    tubewell_id: int,
    reading_type: str,
    meter_id: int | None = None,
) -> Reading | None:

    if reading_type not in (
        "energy",
        "prepaid",
    ):
        raise ValueError(
            "Reading type must be energy or prepaid."
        )

    query = select(
        Reading
    ).where(
        Reading.tubewell_id
        == tubewell_id,

        Reading.reading_type
        == reading_type,
    )

    if meter_id is not None:
        query = query.where(
            Reading.meter_id
            == meter_id
        )

    query = query.order_by(
        Reading.reading_date.desc(),
        Reading.id.desc(),
    )

    return db.scalar(
        query.limit(1)
    )


# ============================================================
# SECTION 4: CALCULATE MISSING READING WARNING
# ============================================================

def calculate_missing_reading_warning(
    *,
    latest_reading: Reading | None,
    today: date | None = None,
) -> dict:

    current_date = (
        today
        if today is not None
        else date.today()
    )

    if latest_reading is None:

        return {
            "warning": True,
            "days_since_last_reading": None,
            "latest_reading_date": None,
            "message":
                "No reading history found.",
        }

    days_since = (
        current_date
        - latest_reading.reading_date
    ).days

    warning = (
        days_since
        >= MISSING_READING_WARNING_DAYS
    )

    if warning:
        message = (
            f"No reading submitted for "
            f"{days_since} days."
        )

    else:
        message = None

    return {
        "warning": warning,
        "days_since_last_reading":
            days_since,
        "latest_reading_date":
            latest_reading.reading_date,
        "message":
            message,
    }


# ============================================================
# SECTION 5: GET WARNING FOR ONE READING TYPE
# ============================================================

def get_missing_reading_warning(
    db: Session,
    *,
    tubewell_id: int,
    reading_type: str,
    meter_id: int | None = None,
    today: date | None = None,
) -> dict:

    latest = get_latest_reading(
        db,
        tubewell_id=tubewell_id,
        reading_type=reading_type,
        meter_id=meter_id,
    )

    result = calculate_missing_reading_warning(
        latest_reading=latest,
        today=today,
    )

    return {
        "tubewell_id":
            tubewell_id,

        "meter_id":
            meter_id,

        "reading_type":
            reading_type,

        **result,
    }