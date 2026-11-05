# ============================================================
# SECTION 1: IMPORTS
# ============================================================

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.reading_management import (
    validate_energy_reading,
    validate_prepaid_reading,
)

from app.core.roles import UserRole

from app.models.reading import Reading
from app.models.reading_correction_request import (
    ReadingCorrectionRequest,
)
from app.models.user import User


# ============================================================
# SECTION 2: REQUIRED TEXT VALIDATION
# ============================================================

def validate_required_text(
    value: str,
    *,
    field_name: str,
    max_length: int,
) -> str:

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} is required."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            f"{field_name} is required."
        )

    if value != cleaned:
        raise ValueError(
            f"{field_name} must not contain "
            "leading or trailing spaces."
        )

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} is too long."
        )

    return value


# ============================================================
# SECTION 3: OPTIONAL REVIEW COMMENT VALIDATION
# ============================================================

def validate_review_comment(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(
            "Review comment must be text."
        )

    cleaned = value.strip()

    if value != cleaned:
        raise ValueError(
            "Review comment must not contain "
            "leading or trailing spaces."
        )

    if len(value) > 500:
        raise ValueError(
            "Review comment is too long."
        )

    if not value:
        return None

    return value


# ============================================================
# SECTION 4: FIND PENDING CORRECTION REQUEST
# ============================================================

def get_pending_reading_correction_request(
    db: Session,
    *,
    reading_id: int,
) -> ReadingCorrectionRequest | None:

    return db.scalar(
        select(ReadingCorrectionRequest).where(
            ReadingCorrectionRequest.reading_id
            == reading_id,
            ReadingCorrectionRequest.status
            == "pending",
        )
    )


# ============================================================
# SECTION 5: VALIDATE READING OWNERSHIP
# ============================================================

def validate_reading_correction_access(
    db: Session,
    *,
    reading_id: int,
    field_user_id: int,
) -> Reading:

    reading = db.get(
        Reading,
        reading_id,
    )

    if reading is None:
        raise ValueError(
            "Reading not found."
        )

    if (
        reading.collected_by_user_id
        != field_user_id
    ):
        raise ValueError(
            "Field User is not authorized to request "
            "correction for this reading."
        )

    return reading


# ============================================================
# SECTION 6: VALIDATE ENERGY CORRECTION
# ============================================================

def validate_energy_correction(
    correction: dict,
) -> dict:

    values = validate_energy_reading(
        previous_reading=correction[
            "previous_reading"
        ],
        current_reading=correction[
            "current_reading"
        ],
        l1=correction["l1"],
        l2=correction["l2"],
        l3=correction["l3"],
        zero_confirmed=correction[
            "zero_confirmed"
        ],
    )

    return {
        "reading_type": "energy",
        "previous_reading": str(
            values["previous_reading"]
        ),
        "current_reading": str(
            values["current_reading"]
        ),
        "l1": str(
            values["l1"]
        ),
        "l2": str(
            values["l2"]
        ),
        "l3": str(
            values["l3"]
        ),
        "zero_confirmed": values[
            "zero_confirmed"
        ],
    }


# ============================================================
# SECTION 7: VALIDATE PREPAID CORRECTION
# ============================================================

def validate_prepaid_correction(
    correction: dict,
) -> dict:

    values = validate_prepaid_reading(
        prepaid_meter_body_number=correction[
            "prepaid_meter_body_number"
        ],
        previous_reading=correction[
            "previous_reading"
        ],
        current_reading=correction[
            "current_reading"
        ],
        previous_money=correction[
            "previous_money"
        ],
        current_money=correction[
            "current_money"
        ],
        previous_time_minutes=correction[
            "previous_time_minutes"
        ],
        current_time_minutes=correction[
            "current_time_minutes"
        ],
    )

    return {
        "reading_type": "prepaid",
        "prepaid_meter_body_number": values[
            "prepaid_meter_body_number"
        ],
        "previous_reading": str(
            values["previous_reading"]
        ),
        "current_reading": str(
            values["current_reading"]
        ),
        "previous_money": str(
            values["previous_money"]
        ),
        "current_money": str(
            values["current_money"]
        ),
        "previous_time_minutes": values[
            "previous_time_minutes"
        ],
        "current_time_minutes": values[
            "current_time_minutes"
        ],
    }


# ============================================================
# SECTION 8: VALIDATE COMPLETE CORRECTION REQUEST
# ============================================================

def validate_reading_correction_request(
    db: Session,
    *,
    reading_id: int,
    field_user_id: int,
    correction: dict,
    reason: str,
) -> dict:

    reading = validate_reading_correction_access(
        db,
        reading_id=reading_id,
        field_user_id=field_user_id,
    )

    existing_pending = (
        get_pending_reading_correction_request(
            db,
            reading_id=reading_id,
        )
    )

    if existing_pending is not None:
        raise ValueError(
            "A pending reading correction request "
            "already exists for this reading."
        )

    if not isinstance(
        correction,
        dict,
    ):
        raise ValueError(
            "Correction payload is invalid."
        )

    correction_type = correction.get(
        "reading_type"
    )

    if correction_type != reading.reading_type:
        raise ValueError(
            "Correction reading type does not match "
            "the original reading type."
        )

    if reading.reading_type == "energy":

        validated_correction = (
            validate_energy_correction(
                correction
            )
        )

    elif reading.reading_type == "prepaid":

        validated_correction = (
            validate_prepaid_correction(
                correction
            )
        )

    else:
        raise ValueError(
            "Unsupported reading type."
        )

    valid_reason = validate_required_text(
        reason,
        field_name="Reason",
        max_length=500,
    )

    return {
        "reading_id": reading_id,
        "requested_by_user_id":
            field_user_id,
        "correction_payload":
            validated_correction,
        "reason":
            valid_reason,
    }


# ============================================================
# SECTION 9: CREATE CORRECTION REQUEST
# ============================================================

def create_reading_correction_request(
    db: Session,
    *,
    reading_id: int,
    field_user_id: int,
    correction: dict,
    reason: str,
) -> ReadingCorrectionRequest:

    values = validate_reading_correction_request(
        db,
        reading_id=reading_id,
        field_user_id=field_user_id,
        correction=correction,
        reason=reason,
    )

    payload_json = json.dumps(
        values["correction_payload"],
        ensure_ascii=False,
        separators=(",", ":"),
    )

    request = ReadingCorrectionRequest(
        reading_id=values[
            "reading_id"
        ],
        requested_by_user_id=values[
            "requested_by_user_id"
        ],
        correction_payload=payload_json,
        reason=values[
            "reason"
        ],
        status="pending",
        reviewed_by_user_id=None,
        reviewed_at=None,
        review_comment=None,
    )

    db.add(request)

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        existing_pending = (
            get_pending_reading_correction_request(
                db,
                reading_id=reading_id,
            )
        )

        if existing_pending is not None:
            raise ValueError(
                "A pending reading correction request "
                "already exists for this reading."
            )

        raise ValueError(
            "Reading correction request "
            "could not be saved."
        )

    db.refresh(request)

    return request


# ============================================================
# SECTION 10: GET PENDING REQUEST FOR SUPERVISOR
# ============================================================

def get_pending_correction_for_supervisor(
    db: Session,
    *,
    request_id: int,
    supervisor_id: int,
) -> ReadingCorrectionRequest:

    if (
        not isinstance(request_id, int)
        or isinstance(request_id, bool)
        or request_id <= 0
    ):
        raise ValueError(
            "Reading correction request not found."
        )

    request_record = db.scalar(
        select(ReadingCorrectionRequest)
        .join(
            User,
            User.id
            == ReadingCorrectionRequest.requested_by_user_id,
        )
        .where(
            ReadingCorrectionRequest.id
            == request_id,

            ReadingCorrectionRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == supervisor_id,
        )
        .with_for_update()
    )

    if request_record is None:
        raise ValueError(
            "Reading correction request not found "
            "or Supervisor is not authorized "
            "to review this request."
        )

    return request_record


# ============================================================
# SECTION 11: APPLY ENERGY CORRECTION
# ============================================================

def apply_energy_correction(
    reading: Reading,
    payload: dict,
) -> None:

    values = validate_energy_reading(
        previous_reading=payload[
            "previous_reading"
        ],
        current_reading=payload[
            "current_reading"
        ],
        l1=payload["l1"],
        l2=payload["l2"],
        l3=payload["l3"],
        zero_confirmed=payload[
            "zero_confirmed"
        ],
    )

    reading.previous_reading = values[
        "previous_reading"
    ]

    reading.current_reading = values[
        "current_reading"
    ]

    reading.l1 = values["l1"]
    reading.l2 = values["l2"]
    reading.l3 = values["l3"]

    reading.zero_confirmed = values[
        "zero_confirmed"
    ]

    reading.prepaid_meter_body_number = None
    reading.previous_money = None
    reading.current_money = None
    reading.previous_time_minutes = None
    reading.current_time_minutes = None


# ============================================================
# SECTION 12: APPLY PREPAID CORRECTION
# ============================================================

def apply_prepaid_correction(
    reading: Reading,
    payload: dict,
) -> None:

    values = validate_prepaid_reading(
        prepaid_meter_body_number=payload[
            "prepaid_meter_body_number"
        ],
        previous_reading=payload[
            "previous_reading"
        ],
        current_reading=payload[
            "current_reading"
        ],
        previous_money=payload[
            "previous_money"
        ],
        current_money=payload[
            "current_money"
        ],
        previous_time_minutes=payload[
            "previous_time_minutes"
        ],
        current_time_minutes=payload[
            "current_time_minutes"
        ],
    )

    reading.previous_reading = values[
        "previous_reading"
    ]

    reading.current_reading = values[
        "current_reading"
    ]

    reading.prepaid_meter_body_number = values[
        "prepaid_meter_body_number"
    ]

    reading.previous_money = values[
        "previous_money"
    ]

    reading.current_money = values[
        "current_money"
    ]

    reading.previous_time_minutes = values[
        "previous_time_minutes"
    ]

    reading.current_time_minutes = values[
        "current_time_minutes"
    ]

    reading.l1 = None
    reading.l2 = None
    reading.l3 = None
    reading.zero_confirmed = None


# ============================================================
# SECTION 13: REVIEW CORRECTION REQUEST
# ============================================================

def review_reading_correction_request(
    db: Session,
    *,
    request_id: int,
    supervisor_id: int,
    action: str,
    review_comment: str | None = None,
) -> ReadingCorrectionRequest:

    if action not in (
        "approved",
        "rejected",
    ):
        raise ValueError(
            "Review action must be approved or rejected."
        )

    valid_comment = validate_review_comment(
        review_comment
    )

    # Rejection requires a meaningful reason, even for direct service calls.
    if action == "rejected" and not valid_comment:
        raise ValueError("Rejection reason is required.")

    request_record = (
        get_pending_correction_for_supervisor(
            db,
            request_id=request_id,
            supervisor_id=supervisor_id,
        )
    )

    review_time = datetime.now()

    # --------------------------------------------------------
    # REJECTION
    # Original Reading stays unchanged.
    # --------------------------------------------------------

    if action == "rejected":

        request_record.status = (
            "rejected"
        )

        request_record.reviewed_by_user_id = (
            supervisor_id
        )

        request_record.reviewed_at = (
            review_time
        )

        request_record.review_comment = (
            valid_comment
        )

        try:
            db.commit()

        except Exception:
            db.rollback()
            raise

        db.refresh(
            request_record
        )

        return request_record

    # --------------------------------------------------------
    # APPROVAL
    # Lock original reading before applying correction.
    # --------------------------------------------------------

    reading = db.scalar(
        select(Reading)
        .where(
            Reading.id
            == request_record.reading_id
        )
        .with_for_update()
    )

    if reading is None:
        raise ValueError(
            "Reading not found."
        )

    try:
        payload = json.loads(
            request_record.correction_payload
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):
        raise ValueError(
            "Stored correction payload is invalid."
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Stored correction payload is invalid."
        )

    if payload.get(
        "reading_type"
    ) != reading.reading_type:
        raise ValueError(
            "Correction reading type does not match "
            "the original reading type."
        )

    if reading.reading_type == "energy":

        apply_energy_correction(
            reading,
            payload,
        )

    elif reading.reading_type == "prepaid":

        apply_prepaid_correction(
            reading,
            payload,
        )

    else:
        raise ValueError(
            "Unsupported reading type."
        )

    request_record.status = (
        "approved"
    )

    request_record.reviewed_by_user_id = (
        supervisor_id
    )

    request_record.reviewed_at = (
        review_time
    )

    request_record.review_comment = (
        valid_comment
    )

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(
        request_record
    )

    return request_record