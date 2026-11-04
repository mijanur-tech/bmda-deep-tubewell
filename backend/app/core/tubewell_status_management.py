# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.reading_management import (
    validate_reading_submission_access,
)

from app.core.roles import UserRole

from app.models.tubewell import Tubewell
from app.models.tubewell_status_request import (
    TubewellStatusRequest,
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
# SECTION 4: FIND PENDING STATUS REQUEST
# ============================================================

def get_pending_tubewell_status_request(
    db: Session,
    *,
    tubewell_id: int,
) -> TubewellStatusRequest | None:

    return db.scalar(
        select(TubewellStatusRequest).where(
            TubewellStatusRequest.tubewell_id
            == tubewell_id,
            TubewellStatusRequest.status.in_(("pending", "pending_ae_approval")),
        )
    )


# ============================================================
# SECTION 5: VALIDATE FIELD USER ACCESS
# ============================================================

def validate_tubewell_status_request_access(
    db: Session,
    *,
    tubewell_id: int,
    field_user_id: int,
) -> Tubewell:

    if not validate_reading_submission_access(
        db,
        tubewell_id,
        field_user_id,
    ):
        raise ValueError(
            "Field User is not authorized to request "
            "a status change for this tubewell."
        )

    tubewell = db.get(
        Tubewell,
        tubewell_id,
    )

    if tubewell is None:
        raise ValueError(
            "Tubewell not found."
        )

    return tubewell


# ============================================================
# SECTION 6: VALIDATE COMPLETE STATUS REQUEST
# ============================================================

def validate_tubewell_status_request(
    db: Session,
    *,
    tubewell_id: int,
    field_user_id: int,
    requested_status: str,
    reason: str,
) -> dict:

    tubewell = validate_tubewell_status_request_access(
        db,
        tubewell_id=tubewell_id,
        field_user_id=field_user_id,
    )

    if requested_status not in (
        "active",
        "inactive",
    ):
        raise ValueError(
            "Requested status must be active or inactive."
        )

    current_status = (
        "active"
        if tubewell.is_active
        else "inactive"
    )

    if requested_status == current_status:
        raise ValueError(
            "Tubewell is already in the requested status."
        )

    existing_pending = (
        get_pending_tubewell_status_request(
            db,
            tubewell_id=tubewell_id,
        )
    )

    if existing_pending is not None:
        raise ValueError(
            "A pending tubewell status request "
            "already exists for this tubewell."
        )

    valid_reason = validate_required_text(
        reason,
        field_name="Reason",
        max_length=500,
    )

    return {
        "tubewell_id": tubewell_id,
        "requested_by_user_id":
            field_user_id,
        "requested_status":
            requested_status,
        "reason":
            valid_reason,
    }


# ============================================================
# SECTION 7: CREATE STATUS REQUEST
# ============================================================

def create_tubewell_status_request(
    db: Session,
    *,
    tubewell_id: int,
    field_user_id: int,
    requested_status: str,
    reason: str,
) -> TubewellStatusRequest:

    values = validate_tubewell_status_request(
        db,
        tubewell_id=tubewell_id,
        field_user_id=field_user_id,
        requested_status=requested_status,
        reason=reason,
    )

    request = TubewellStatusRequest(
        tubewell_id=values[
            "tubewell_id"
        ],
        requested_by_user_id=values[
            "requested_by_user_id"
        ],
        requested_status=values[
            "requested_status"
        ],
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
            get_pending_tubewell_status_request(
                db,
                tubewell_id=tubewell_id,
            )
        )

        if existing_pending is not None:
            raise ValueError(
                "A pending tubewell status request "
                "already exists for this tubewell."
            )

        raise ValueError(
            "Tubewell status request could not be saved."
        )

    db.refresh(request)

    return request


# ============================================================
# SECTION 8: GET PENDING REQUEST FOR SUPERVISOR REVIEW
# ============================================================

def get_pending_status_request_for_supervisor(
    db: Session,
    *,
    request_id: int,
    supervisor_id: int,
) -> TubewellStatusRequest:

    if (
        not isinstance(request_id, int)
        or isinstance(request_id, bool)
        or request_id <= 0
    ):
        raise ValueError(
            "Tubewell status request not found."
        )

    replacement_request = db.scalar(
        select(TubewellStatusRequest)
        .join(
            User,
            User.id
            == TubewellStatusRequest.requested_by_user_id,
        )
        .where(
            TubewellStatusRequest.id
            == request_id,

            TubewellStatusRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == supervisor_id,
            User.upazila_id == select(User.upazila_id).where(User.id == supervisor_id).scalar_subquery(),
        )
        .with_for_update()
    )

    if replacement_request is None:
        raise ValueError(
            "Tubewell status request not found "
            "or Supervisor is not authorized "
            "to review this request."
        )

    return replacement_request


# ============================================================
# SECTION 9: REVIEW STATUS REQUEST
#
# APPROVED:
# - update Tubewell.is_active
#
# REJECTED:
# - leave Tubewell.is_active unchanged
#
# Inactive tubewells still allow reading submission.
# ============================================================

def review_tubewell_status_request(
    db: Session,
    *,
    request_id: int,
    supervisor_id: int,
    action: str,
    review_comment: str | None = None,
) -> TubewellStatusRequest:

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

    request_record = (
        get_pending_status_request_for_supervisor(
            db,
            request_id=request_id,
            supervisor_id=supervisor_id,
        )
    )

    review_time = datetime.now()

    # --------------------------------------------------------
    # REJECTION
    # Tubewell operational status remains unchanged.
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

    # Supervisor forwards; only AE final approval changes Tubewell.
    request_record.status = "pending_ae_approval"
    request_record.reviewed_by_user_id = supervisor_id
    request_record.reviewed_at = review_time
    request_record.review_comment = valid_comment
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(request_record)
    return request_record


def review_tubewell_status_request_by_ae(
    db: Session, *, request_id: int, ae_id: int,
    action: str, review_comment: str | None = None,
) -> TubewellStatusRequest:
    if action not in ("approved", "rejected"):
        raise ValueError("Review action must be approved or rejected.")
    comment = validate_review_comment(review_comment)
    ae = db.get(User, ae_id)
    if ae is None or ae.role != UserRole.ASSISTANT_ENGINEER.value or ae.upazila_id is None:
        raise ValueError("AE is not authorized.")
    record = db.scalar(
        select(TubewellStatusRequest)
        .join(Tubewell, Tubewell.id == TubewellStatusRequest.tubewell_id)
        .where(TubewellStatusRequest.id == request_id,
               TubewellStatusRequest.status == "pending_ae_approval",
               Tubewell.management_unit_id == ae.upazila_id)
        .with_for_update(of=TubewellStatusRequest)
    )
    if record is None:
        raise ValueError("Request not found or AE is not authorized.")
    if action == "approved":
        tubewell = db.scalar(select(Tubewell).where(
            Tubewell.id == record.tubewell_id,
            Tubewell.management_unit_id == ae.upazila_id,
        ).with_for_update())
        if tubewell is None:
            raise ValueError("Tubewell not found.")
        if record.requested_status not in ("active", "inactive"):
            raise ValueError("Unsupported requested status.")
        tubewell.is_active = record.requested_status == "active"
    record.status = action
    record.ae_reviewed_by_user_id = ae_id
    record.ae_reviewed_at = datetime.now()
    record.ae_review_comment = comment
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record
