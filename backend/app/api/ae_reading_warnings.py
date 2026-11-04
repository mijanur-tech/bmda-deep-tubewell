
# ============================================================
# BMDA AE DASHBOARD — READING WARNINGS
# Read-only, AE-only, management-unit scoped.
# ============================================================

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.reading_warning_management import (
    MISSING_READING_WARNING_DAYS,
)
from app.db.database import get_db
from app.models.meter import Meter
from app.models.reading import Reading
from app.models.tubewell import Tubewell
from app.models.tubewell_status_request import TubewellStatusRequest
from app.models.user import User


router = APIRouter(
    prefix="/dashboard/ae",
    tags=["AE Dashboard"],
)


@router.get("/reading-warnings")
def get_ae_reading_warnings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. AE-only authorization.
    if current_user.role != "assistant_engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assistant Engineer access is required.",
        )

    unit_id = current_user.upazila_id

    if unit_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Management unit assignment is required.",
        )

    today = datetime.now(
        ZoneInfo("Asia/Dhaka")
    ).date()

    # 2. Registered tubewells without any reading history.
    # Informational only, not an overdue warning.
    all_tubewell_ids = set(
        db.scalars(
            select(Tubewell.id).where(
                Tubewell.management_unit_id == unit_id
            )
        ).all()
    )

    tubewells_with_history = set(
        db.scalars(
            select(Reading.tubewell_id)
            .join(
                Tubewell,
                Reading.tubewell_id == Tubewell.id,
            )
            .where(
                Tubewell.management_unit_id == unit_id
            )
            .distinct()
        ).all()
    )

    reading_not_started = len(
        all_tubewell_ids - tubewells_with_history
    )

    # 3. Registered, non-removed meters on active tubewells.
    # A blank removed_at alone is not proof of registration.
    meters = db.execute(
        select(
            Meter.id,
            Meter.tubewell_id,
            Meter.meter_type,
        )
        .join(
            Tubewell,
            Tubewell.id == Meter.tubewell_id,
        )
        .where(
            Tubewell.management_unit_id == unit_id,
            Tubewell.is_active.is_(True),
            Meter.removed_at.is_(None),
            Meter.meter_number.is_not(None),
            func.length(
                func.trim(Meter.meter_number)
            ) > 0,
            Meter.meter_type.in_(
                ("energy", "prepaid")
            ),
        )
    ).all()

    # 4. Find latest approved reactivation per tubewell.
    # Only AE-approved transitions to ACTIVE are applicable.
    reactivation_rows = db.execute(
        select(
            TubewellStatusRequest.tubewell_id,
            func.max(
                TubewellStatusRequest.ae_reviewed_at
            ),
        )
        .join(
            Tubewell,
            Tubewell.id == TubewellStatusRequest.tubewell_id,
        )
        .where(
            Tubewell.management_unit_id == unit_id,
            TubewellStatusRequest.requested_status == "active",
            TubewellStatusRequest.status == "approved",
            TubewellStatusRequest.ae_reviewed_at.is_not(None),
        )
        .group_by(
            TubewellStatusRequest.tubewell_id
        )
    ).all()

    reactivation_dates = {
        tubewell_id: approved_at.date()
        for tubewell_id, approved_at in reactivation_rows
        if approved_at is not None
    }

    # 5. Latest meter-linked readings, separated by meter type.
    # Legacy readings with no meter_id are not reassigned
    # automatically to a newly registered meter.
    meter_ids = [
        meter_id
        for meter_id, _, _ in meters
    ]

    latest_readings = {}

    if meter_ids:
        reading_rows = db.execute(
            select(
                Reading.meter_id,
                Reading.reading_type,
                func.max(
                    Reading.reading_date
                ),
            )
            .where(
                Reading.meter_id.in_(meter_ids),
                Reading.reading_type.in_(
                    ("energy", "prepaid")
                ),
            )
            .group_by(
                Reading.meter_id,
                Reading.reading_type,
            )
        ).all()

        latest_readings = {
            (meter_id, reading_type): latest_date
            for meter_id, reading_type, latest_date
            in reading_rows
        }

    # 6. Calculate warnings after the applicable first reading.
    # Reactivation invalidates older readings for countdown purposes.
    energy_warning_ids = set()
    prepaid_warning_ids = set()

    for meter_id, tubewell_id, meter_type in meters:
        latest_date = latest_readings.get(
            (meter_id, meter_type)
        )

        if latest_date is None:
            continue

        reactivated_on = reactivation_dates.get(
            tubewell_id
        )

        # No post-reactivation reading yet:
        # countdown has not started.
        if (
            reactivated_on is not None
            and latest_date < reactivated_on
        ):
            continue

        days_since = (
            today - latest_date
        ).days

        if days_since < MISSING_READING_WARNING_DAYS:
            continue

        if meter_type == "energy":
            energy_warning_ids.add(tubewell_id)

        elif meter_type == "prepaid":
            prepaid_warning_ids.add(tubewell_id)

    # 7. Distinct tubewell count prevents double counting.
    overdue_tubewell_ids = (
        energy_warning_ids | prepaid_warning_ids
    )

    # 8. Preserve existing API response structure.
    return {
        "management_unit_id": unit_id,
        "overdue_tubewells": len(overdue_tubewell_ids),
        "energy_warnings": len(energy_warning_ids),
        "prepaid_warnings": len(prepaid_warning_ids),
        "reading_not_started": reading_not_started,
        "warning_threshold_days": MISSING_READING_WARNING_DAYS,
    }
