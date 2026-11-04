# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import UserRole

from app.models.meter_replacement_request import (
    MeterReplacementRequest,
)

from app.models.reading import Reading

from app.models.reading_correction_request import (
    ReadingCorrectionRequest,
)

from app.models.tubewell_status_request import (
    TubewellStatusRequest,
)

from app.models.user import User


# ============================================================
# SECTION 2: METER REPLACEMENT PENDING REQUESTS
# ============================================================

def get_pending_meter_replacements(
    db: Session,
    *,
    supervisor_id: int,
) -> list[dict]:

    query = (
        select(MeterReplacementRequest)
        .join(
            User,
            User.id
            == MeterReplacementRequest.requested_by_user_id,
        )
        .where(
            MeterReplacementRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == supervisor_id,
        )
    )

    rows = db.scalars(
        query
    ).all()

    return [
        {
            "request_type":
                "meter_replacement",

            "request_id":
                row.id,

            "tubewell_id":
                row.tubewell_id,

            "reading_id":
                None,

            "requested_by_user_id":
                row.requested_by_user_id,

            "reason":
                row.reason,

            "status":
                "pending",

            "requested_at":
                row.requested_at,

            "requested_status":
                None,

            "old_meter_id":
                row.old_meter_id,

            "new_meter_number":
                row.new_meter_number,

            "reading_type":
                None,
        }
        for row in rows
    ]


# ============================================================
# SECTION 3: TUBEWELL STATUS PENDING REQUESTS
# ============================================================

def get_pending_tubewell_status_requests(
    db: Session,
    *,
    supervisor_id: int,
) -> list[dict]:

    query = (
        select(TubewellStatusRequest)
        .join(
            User,
            User.id
            == TubewellStatusRequest.requested_by_user_id,
        )
        .where(
            TubewellStatusRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == supervisor_id,
        )
    )

    rows = db.scalars(
        query
    ).all()

    return [
        {
            "request_type":
                "tubewell_status",

            "request_id":
                row.id,

            "tubewell_id":
                row.tubewell_id,

            "reading_id":
                None,

            "requested_by_user_id":
                row.requested_by_user_id,

            "reason":
                row.reason,

            "status":
                "pending",

            "requested_at":
                row.requested_at,

            "requested_status":
                row.requested_status,

            "old_meter_id":
                None,

            "new_meter_number":
                None,

            "reading_type":
                None,
        }
        for row in rows
    ]


# ============================================================
# SECTION 4: READING CORRECTION PENDING REQUESTS
# ============================================================

def get_pending_reading_corrections(
    db: Session,
    *,
    supervisor_id: int,
) -> list[dict]:

    query = (
        select(
            ReadingCorrectionRequest,
            Reading,
        )
        .join(
            User,
            User.id
            == ReadingCorrectionRequest.requested_by_user_id,
        )
        .join(
            Reading,
            Reading.id
            == ReadingCorrectionRequest.reading_id,
        )
        .where(
            ReadingCorrectionRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == supervisor_id,
        )
    )

    rows = db.execute(
        query
    ).all()

    return [
        {
            "request_type":
                "reading_correction",

            "request_id":
                request_record.id,

            "tubewell_id":
                reading.tubewell_id,

            "reading_id":
                reading.id,

            "requested_by_user_id":
                request_record.requested_by_user_id,

            "reason":
                request_record.reason,

            "status":
                "pending",

            "requested_at":
                request_record.requested_at,

            "requested_status":
                None,

            "old_meter_id":
                None,

            "new_meter_number":
                None,

            "reading_type":
                reading.reading_type,
        }
        for request_record, reading in rows
    ]


# ============================================================
# SECTION 5: COMBINED PENDING REQUEST QUEUE
# ============================================================

def get_combined_pending_requests(
    db: Session,
    *,
    supervisor_id: int,
) -> list[dict]:

    if (
        not isinstance(supervisor_id, int)
        or isinstance(supervisor_id, bool)
        or supervisor_id <= 0
    ):
        raise ValueError(
            "Invalid Supervisor ID."
        )

    combined = []

    combined.extend(
        get_pending_meter_replacements(
            db,
            supervisor_id=supervisor_id,
        )
    )

    combined.extend(
        get_pending_tubewell_status_requests(
            db,
            supervisor_id=supervisor_id,
        )
    )

    combined.extend(
        get_pending_reading_corrections(
            db,
            supervisor_id=supervisor_id,
        )
    )

    combined.sort(
        key=lambda item: (
            item["requested_at"],
            item["request_id"],
        ),
        reverse=True,
    )

    return combined