# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.reading_management import (
    validate_reading_submission_access,
)

from app.core.roles import UserRole

from app.models.meter import Meter
from app.models.tubewell import Tubewell
from app.models.meter_replacement_request import (
    MeterReplacementRequest,
)
from app.models.user import User


# ============================================================
# SECTION 2: TEXT VALIDATION
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
# SECTION 4: VALIDATE OLD METER
# ============================================================

def validate_old_meter_for_tubewell(
    db: Session,
    *,
    tubewell_id: int,
    old_meter_id: int,
) -> Meter:

    meter = db.get(
        Meter,
        old_meter_id,
    )

    if meter is None:
        raise ValueError(
            "Old meter not found."
        )

    if meter.tubewell_id != tubewell_id:
        raise ValueError(
            "Old meter does not belong to this tubewell."
        )

    if meter.meter_type not in ("energy", "prepaid"):
        raise ValueError("Old meter type must be energy or prepaid.")

    return meter


# ============================================================
# SECTION 5: FIND PENDING REQUEST
# ============================================================

def get_pending_meter_replacement_request(
    db: Session,
    *,
    tubewell_id: int,
    meter_type: str,
) -> MeterReplacementRequest | None:

    return db.scalar(
        select(MeterReplacementRequest).where(
            MeterReplacementRequest.tubewell_id
            == tubewell_id,
            MeterReplacementRequest.meter_type == meter_type,
            MeterReplacementRequest.status.in_(
                ("pending", "pending_ae_approval")
            ),
        )
    )


# ============================================================
# SECTION 6: VALIDATE FIELD USER REQUEST ACCESS
# ============================================================

def validate_meter_replacement_request_access(
    db: Session,
    *,
    tubewell_id: int,
    field_user_id: int,
) -> None:

    if not validate_reading_submission_access(
        db,
        tubewell_id,
        field_user_id,
    ):
        raise ValueError(
            "Field User is not authorized to request "
            "meter replacement for this tubewell."
        )


# ============================================================
# SECTION 7: VALIDATE COMPLETE REQUEST
# ============================================================

def validate_meter_replacement_request(
    db: Session,
    *,
    tubewell_id: int,
    old_meter_id: int,
    field_user_id: int,
    new_meter_number: str,
    reason: str,
) -> dict:

    validate_meter_replacement_request_access(
        db,
        tubewell_id=tubewell_id,
        field_user_id=field_user_id,
    )

    old_meter = validate_old_meter_for_tubewell(
        db,
        tubewell_id=tubewell_id,
        old_meter_id=old_meter_id,
    )

    if old_meter.removed_at is not None:
        raise ValueError("Old meter has already been removed.")

    existing_pending = (
        get_pending_meter_replacement_request(
            db,
            tubewell_id=tubewell_id,
            meter_type=old_meter.meter_type,
        )
    )

    if existing_pending is not None:
        raise ValueError(
            "A pending meter replacement request "
            "already exists for this tubewell."
        )

    valid_new_meter_number = (
        validate_required_text(
            new_meter_number,
            field_name="New meter number",
            max_length=100,
        )
    )

    if (
        old_meter.meter_number is not None
        and valid_new_meter_number
        == old_meter.meter_number
    ):
        raise ValueError(
            "New meter number must be different "
            "from the old meter number."
        )

    valid_reason = validate_required_text(
        reason,
        field_name="Reason",
        max_length=500,
    )

    return {
        "tubewell_id": tubewell_id,
        "old_meter_id": old_meter_id,
        "meter_type": old_meter.meter_type,
        "requested_by_user_id":
            field_user_id,
        "new_meter_number":
            valid_new_meter_number,
        "reason":
            valid_reason,
    }


# ============================================================
# SECTION 8: CREATE REPLACEMENT REQUEST
# ============================================================

def create_meter_replacement_request(
    db: Session,
    *,
    tubewell_id: int,
    old_meter_id: int,
    field_user_id: int,
    new_meter_number: str,
    reason: str,
) -> MeterReplacementRequest:

    values = validate_meter_replacement_request(
        db,
        tubewell_id=tubewell_id,
        old_meter_id=old_meter_id,
        field_user_id=field_user_id,
        new_meter_number=new_meter_number,
        reason=reason,
    )

    request = MeterReplacementRequest(
        tubewell_id=values[
            "tubewell_id"
        ],
        old_meter_id=values[
            "old_meter_id"
        ],
        meter_type=values["meter_type"],
        requested_by_user_id=values[
            "requested_by_user_id"
        ],
        new_meter_number=values[
            "new_meter_number"
        ],
        reason=values[
            "reason"
        ],
        status="pending",
        reviewed_by_user_id=None,
        reviewed_at=None,
        review_comment=None,
        new_meter_id=None,
    )

    db.add(request)

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        existing_pending = (
            get_pending_meter_replacement_request(
                db,
                tubewell_id=tubewell_id,
                meter_type=values["meter_type"],
            )
        )

        if existing_pending is not None:
            raise ValueError(
                "A pending meter replacement request "
                "already exists for this tubewell."
            )

        raise ValueError(
            "Meter replacement request "
            "could not be saved."
        )

    db.refresh(request)

    return request


# ============================================================
# SECTION 9: GET PENDING REQUEST FOR SUPERVISOR REVIEW
#
# Row lock prevents two review operations from approving or
# rejecting the same pending request simultaneously.
# ============================================================

def get_pending_request_for_supervisor(
    db: Session,
    *,
    request_id: int,
    supervisor_id: int,
) -> MeterReplacementRequest:

    if (
        not isinstance(request_id, int)
        or isinstance(request_id, bool)
        or request_id <= 0
    ):
        raise ValueError(
            "Meter replacement request not found."
        )

    if (
        not isinstance(supervisor_id, int)
        or isinstance(supervisor_id, bool)
        or supervisor_id <= 0
    ):
        raise ValueError(
            "Supervisor is not authorized "
            "to review this request."
        )

    replacement_request = db.scalar(
        select(MeterReplacementRequest)
        .join(
            User,
            User.id
            == MeterReplacementRequest.requested_by_user_id,
        )
        .where(
            MeterReplacementRequest.id
            == request_id,
            MeterReplacementRequest.status
            == "pending",
            User.role
            == UserRole.FIELD_USER.value,
            User.supervisor_id
            == supervisor_id,
        )
        .with_for_update()
    )

    if replacement_request is None:
        raise ValueError(
            "Meter replacement request not found "
            "or Supervisor is not authorized "
            "to review this request."
        )

    return replacement_request


# ============================================================
# SECTION 10: SAE REVIEW (RECOMMENDATION ONLY)
# ============================================================

def review_meter_replacement_request(
    db: Session,
    *,
    request_id: int,
    supervisor_id: int,
    action: str,
    review_comment: str | None = None,
) -> MeterReplacementRequest:

    if action not in ("approved", "rejected"):
        raise ValueError("Review action must be approved or rejected.")

    valid_comment = validate_review_comment(review_comment)
    replacement_request = get_pending_request_for_supervisor(
        db,
        request_id=request_id,
        supervisor_id=supervisor_id,
    )

    # Recheck the original meter before forwarding to AE.
    if action == "approved":
        old_meter = validate_old_meter_for_tubewell(
            db,
            tubewell_id=replacement_request.tubewell_id,
            old_meter_id=replacement_request.old_meter_id,
        )
        if old_meter.removed_at is not None:
            raise ValueError("Old meter has already been removed.")
        if old_meter.meter_type != replacement_request.meter_type:
            raise ValueError("Old meter type does not match the replacement request.")

    # SAE rejection ends the request. SAE approval only forwards it.
    replacement_request.status = (
        "pending_ae_approval" if action == "approved" else "rejected"
    )
    replacement_request.reviewed_by_user_id = supervisor_id
    replacement_request.reviewed_at = datetime.now()
    replacement_request.review_comment = valid_comment
    replacement_request.new_meter_id = None

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(replacement_request)
    return replacement_request


# ============================================================
# SECTION 11: AE FINAL REVIEW
# ============================================================

def review_meter_replacement_request_by_ae(
    db: Session,
    *,
    request_id: int,
    ae_id: int,
    action: str,
    review_comment: str | None = None,
) -> MeterReplacementRequest:

    if action not in ("approved", "rejected"):
        raise ValueError("Review action must be approved or rejected.")

    valid_comment = validate_review_comment(review_comment)

    if not isinstance(ae_id, int) or isinstance(ae_id, bool) or ae_id <= 0:
        raise ValueError("AE is not authorized.")
    if not isinstance(request_id, int) or isinstance(request_id, bool) or request_id <= 0:
        raise ValueError("Request not found or AE is not authorized.")

    ae = db.get(User, ae_id)
    if (
        ae is None
        or ae.role != UserRole.ASSISTANT_ENGINEER.value
        or ae.upazila_id is None
        or not ae.is_active
    ):
        raise ValueError("AE is not authorized.")

    replacement_request = db.scalar(
        select(MeterReplacementRequest)
        .join(
            Tubewell,
            Tubewell.id == MeterReplacementRequest.tubewell_id,
        )
        .where(
            MeterReplacementRequest.id == request_id,
            MeterReplacementRequest.status == "pending_ae_approval",
            Tubewell.management_unit_id == ae.upazila_id,
        )
        .with_for_update(of=MeterReplacementRequest)
    )
    if replacement_request is None:
        raise ValueError("Request not found or AE is not authorized.")

    if action == "approved":
        # Lock the old meter to prevent concurrent final approvals.
        old_meter = db.scalar(
            select(Meter)
            .where(Meter.id == replacement_request.old_meter_id)
            .with_for_update()
        )
        if old_meter is None or old_meter.tubewell_id != replacement_request.tubewell_id:
            raise ValueError("Old meter not found for this tubewell.")
        if old_meter.removed_at is not None:
            raise ValueError("Old meter has already been removed.")
        if old_meter.meter_type != replacement_request.meter_type:
            raise ValueError("Old meter type does not match the replacement request.")

        replacement_date = date.today()
        old_meter.removed_at = replacement_date
        new_meter = Meter(
            tubewell_id=replacement_request.tubewell_id,
            meter_type=replacement_request.meter_type,
            meter_number=replacement_request.new_meter_number,
            installed_at=replacement_date,
            removed_at=None,
        )
        db.add(new_meter)
        try:
            db.flush()
            replacement_request.new_meter_id = new_meter.id
        except Exception:
            db.rollback()
            raise
    else:
        # AE rejection must not change any meter record.
        replacement_request.new_meter_id = None

    replacement_request.status = action
    replacement_request.ae_reviewed_by_user_id = ae_id
    replacement_request.ae_reviewed_at = datetime.now()
    replacement_request.ae_review_comment = valid_comment

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(replacement_request)
    return replacement_request
