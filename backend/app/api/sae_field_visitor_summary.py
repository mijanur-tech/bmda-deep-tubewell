"""
SAE Field Visitor Summary and Tubewell Assignments
Phase 05 — Steps 29.7 and 30.7

Read-only endpoints. No database schema changes.
All results are restricted to the authenticated SAE.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.roles import UserRole
from app.db.database import get_db
from app.models.user import User
from app.models.tubewell import Tubewell
from app.models.tubewell_assignment import TubewellAssignment
from app.models.meter import Meter
from app.models.reading import Reading
from app.models.tubewell_status_request import TubewellStatusRequest
from app.core.reading_warning_management import MISSING_READING_WARNING_DAYS


# ============================================================
# SECTION 1: RESPONSE SCHEMAS
# ============================================================

class SAEFieldVisitorItem(BaseModel):
    field_user_id: int
    full_name: str
    is_active: bool
    assigned_tubewells: int = Field(ge=0)


class SAEFieldVisitorSummary(BaseModel):
    supervisor_id: int
    management_unit_id: int

    total_field_visitors: int = Field(ge=0)
    active_field_visitors: int = Field(ge=0)
    inactive_field_visitors: int = Field(ge=0)

    assigned_tubewells: int = Field(ge=0)
    visitors_without_assignments: int = Field(ge=0)

    field_visitors: list[SAEFieldVisitorItem]


class SAETubewellAssignmentItem(BaseModel):
    assignment_id: int
    field_user_id: int
    field_user_name: str
    field_user_is_active: bool
    tubewell_id: int
    tubewell_number: str
    tubewell_name: str
    tubewell_is_active: bool
    actual_upazila: str | None
    union_name: str | None
    mouza: str | None
    assigned_at: date | None


class SAETubewellAssignmentsResponse(BaseModel):
    supervisor_id: int
    management_unit_id: int
    total_assignments: int = Field(ge=0)
    assignments: list[SAETubewellAssignmentItem]


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/dashboard/sae",
    tags=["SAE Dashboard"],
)


# ============================================================
# SECTION 3: AUTHORIZATION — REUSED BY BOTH ENDPOINTS
# ============================================================

def require_sae(
    current_user: User = Depends(get_current_user),
) -> User:

    if current_user.role != UserRole.SUPERVISOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sub-Assistant Engineer access required.",
        )

    if current_user.upazila_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Management unit is not assigned.",
        )

    return current_user


# ============================================================
# SECTION 4: EXISTING FIELD VISITOR SUMMARY — UNCHANGED
# ============================================================

@router.get(
    "/field-visitor-summary",
    response_model=SAEFieldVisitorSummary,
)
def get_sae_field_visitor_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sae),
):

    # Count only CURRENT assignments.
    # Include only tubewells belonging to the SAE's unit.

    assignment_counts = (
        select(
            TubewellAssignment.field_user_id.label(
                "field_user_id"
            ),
            func.count(
                TubewellAssignment.id
            ).label("assignment_count"),
        )
        .join(
            Tubewell,
            Tubewell.id == TubewellAssignment.tubewell_id,
        )
        .where(
            TubewellAssignment.ended_at.is_(None),
            Tubewell.management_unit_id
            == current_user.upazila_id,
        )
        .group_by(
            TubewellAssignment.field_user_id
        )
        .subquery()
    )

    # Server-side ownership and unit isolation.
    # Inactive Field Visitors remain visible for monitoring.

    query = (
        select(
            User.id,
            User.full_name,
            User.is_active,
            func.coalesce(
                assignment_counts.c.assignment_count,
                0,
            ).label("assigned_tubewells"),
        )
        .outerjoin(
            assignment_counts,
            assignment_counts.c.field_user_id == User.id,
        )
        .where(
            User.role == UserRole.FIELD_USER.value,
            User.supervisor_id == current_user.id,
            User.upazila_id == current_user.upazila_id,
        )
        .order_by(
            User.full_name.asc(),
            User.id.asc(),
        )
    )

    rows = db.execute(query).all()

    field_visitors = [
        SAEFieldVisitorItem(
            field_user_id=row.id,
            full_name=row.full_name,
            is_active=row.is_active,
            assigned_tubewells=int(row.assigned_tubewells),
        )
        for row in rows
    ]

    active_count = sum(
        1 for item in field_visitors if item.is_active
    )

    total_count = len(field_visitors)

    return SAEFieldVisitorSummary(
        supervisor_id=current_user.id,
        management_unit_id=current_user.upazila_id,
        total_field_visitors=total_count,
        active_field_visitors=active_count,
        inactive_field_visitors=total_count - active_count,
        assigned_tubewells=sum(
            item.assigned_tubewells
            for item in field_visitors
        ),
        visitors_without_assignments=sum(
            1
            for item in field_visitors
            if item.assigned_tubewells == 0
        ),
        field_visitors=field_visitors,
    )


# ============================================================
# SECTION 5: CURRENT TUBEWELL ASSIGNMENTS — NEW READ-ONLY API
# ============================================================

@router.get(
    "/tubewell-assignments",
    response_model=SAETubewellAssignmentsResponse,
)
def get_sae_tubewell_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sae),
):
    """List current assignments for field visitors of this SAE only.

    Include inactive field visitors and inactive tubewells: deactivation
    does not cancel an existing current assignment. No history is changed.
    """

    query = (
        select(
            TubewellAssignment.id.label("assignment_id"),
            TubewellAssignment.assigned_at.label("assigned_at"),
            User.id.label("field_user_id"),
            User.full_name.label("field_user_name"),
            User.is_active.label("field_user_is_active"),
            Tubewell.id.label("tubewell_id"),
            Tubewell.tubewell_number.label("tubewell_number"),
            Tubewell.name.label("tubewell_name"),
            Tubewell.is_active.label("tubewell_is_active"),
            Tubewell.actual_upazila.label("actual_upazila"),
            Tubewell.union_name.label("union_name"),
            Tubewell.mouza.label("mouza"),
        )
        .join(
            User,
            User.id == TubewellAssignment.field_user_id,
        )
        .join(
            Tubewell,
            Tubewell.id == TubewellAssignment.tubewell_id,
        )
        .where(
            TubewellAssignment.ended_at.is_(None),
            User.role == UserRole.FIELD_USER.value,
            User.supervisor_id == current_user.id,
            User.upazila_id == current_user.upazila_id,
            Tubewell.management_unit_id == current_user.upazila_id,
        )
        .order_by(
            User.full_name.asc(),
            Tubewell.tubewell_number.asc(),
            TubewellAssignment.id.asc(),
        )
    )

    assignments = [
        SAETubewellAssignmentItem(**row._mapping)
        for row in db.execute(query).all()
    ]

    return SAETubewellAssignmentsResponse(
        supervisor_id=current_user.id,
        management_unit_id=current_user.upazila_id,
        total_assignments=len(assignments),
        assignments=assignments,
    )


# ============================================================
# SECTION 6: SAE READING ACTIVITY — READ ONLY
# ============================================================

class SAEReadingTypeActivity(BaseModel):
    status: str  # not_available, not_started, up_to_date, overdue
    meter_id: int | None = None
    latest_reading_date: date | None = None
    days_since_last_reading: int | None = None
    collected_by_field_visitor: str | None = None
    note: str | None = None


class SAEReadingTubewellActivity(BaseModel):
    tubewell_id: int
    tubewell_number: str
    tubewell_name: str
    tubewell_is_active: bool
    field_user_id: int
    field_user_name: str
    energy: SAEReadingTypeActivity
    prepaid: SAEReadingTypeActivity


class SAEReadingActivityResponse(BaseModel):
    supervisor_id: int
    management_unit_id: int
    warning_threshold_days: int
    total_assigned_tubewells: int = Field(ge=0)
    energy_overdue: int = Field(ge=0)
    prepaid_overdue: int = Field(ge=0)
    overdue_tubewells: int = Field(ge=0)
    tubewells: list[SAEReadingTubewellActivity]


@router.get(
    "/reading-activity",
    response_model=SAEReadingActivityResponse,
)
def get_sae_reading_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sae),
):
    """Current-team tubewells only; no unregistered-meter warnings.

    Mirrors Phase 04 AE rules for eligible meters, first-reading countdown,
    per-meter reading history and approved reactivation. Does not change any
    reading, meter, assignment or status request.
    """
    today = datetime.now(ZoneInfo("Asia/Dhaka")).date()
    unit_id = current_user.upazila_id

    # One current assignment per tubewell is enforced by database index.
    assignments = db.execute(
        select(
            Tubewell.id.label("tubewell_id"),
            Tubewell.tubewell_number,
            Tubewell.name.label("tubewell_name"),
            Tubewell.is_active.label("tubewell_is_active"),
            User.id.label("field_user_id"),
            User.full_name.label("field_user_name"),
        )
        .join(TubewellAssignment, TubewellAssignment.tubewell_id == Tubewell.id)
        .join(User, User.id == TubewellAssignment.field_user_id)
        .where(
            TubewellAssignment.ended_at.is_(None),
            Tubewell.management_unit_id == unit_id,
            User.role == UserRole.FIELD_USER.value,
            User.supervisor_id == current_user.id,
            User.upazila_id == unit_id,
        )
        .order_by(Tubewell.tubewell_number.asc(), Tubewell.id.asc())
    ).all()

    tubewell_ids = [row.tubewell_id for row in assignments]
    meters_by_well_type = {}
    latest_readings = {}
    reactivation_dates = {}

    if tubewell_ids:
        # A meter needs a verified number, a valid type and no removal date.
        meter_rows = db.execute(
            select(Meter.id, Meter.tubewell_id, Meter.meter_type)
            .where(
                Meter.tubewell_id.in_(tubewell_ids),
                Meter.removed_at.is_(None),
                Meter.meter_number.is_not(None),
                func.length(func.trim(Meter.meter_number)) > 0,
                Meter.meter_type.in_(("energy", "prepaid")),
            )
        ).all()

        for meter_id, well_id, meter_type in meter_rows:
            meters_by_well_type.setdefault((well_id, meter_type), []).append(meter_id)

        meter_ids = [row.id for row in meter_rows]
        if meter_ids:
            # Ordered latest-first, with ID as deterministic same-date tiebreaker.
            # A reading belongs to its meter; legacy NULL meter IDs are not reassigned.
            reading_rows = db.execute(
                select(
                    Reading.id,
                    Reading.meter_id,
                    Reading.tubewell_id,
                    Reading.reading_type,
                    Reading.reading_date,
                    Reading.collected_by_user_id,
                )
                .where(
                    Reading.meter_id.in_(meter_ids),
                    Reading.tubewell_id.in_(tubewell_ids),
                    Reading.reading_type.in_(("energy", "prepaid")),
                )
                .order_by(Reading.reading_date.desc(), Reading.id.desc())
            ).all()
            for row in reading_rows:
                latest_readings.setdefault(
                    (row.meter_id, row.tubewell_id, row.reading_type), row
                )

        # Only AE-approved transitions back to active reset the clock.
        reactivation_rows = db.execute(
            select(
                TubewellStatusRequest.tubewell_id,
                func.max(TubewellStatusRequest.ae_reviewed_at),
            )
            .where(
                TubewellStatusRequest.tubewell_id.in_(tubewell_ids),
                TubewellStatusRequest.requested_status == "active",
                TubewellStatusRequest.status == "approved",
                TubewellStatusRequest.ae_reviewed_at.is_not(None),
            )
            .group_by(TubewellStatusRequest.tubewell_id)
        ).all()
        reactivation_dates = {
            well_id: reviewed_at.date()
            for well_id, reviewed_at in reactivation_rows
            if reviewed_at is not None
        }

    def activity_for(row, meter_type):
        if not row.tubewell_is_active:
            return SAEReadingTypeActivity(
                status="not_available", note="Tubewell is inactive; warning countdown paused."
            )

        meter_ids_for_type = meters_by_well_type.get((row.tubewell_id, meter_type), [])
        if not meter_ids_for_type:
            return SAEReadingTypeActivity(
                status="not_available", note="No verified current meter registered."
            )
        if len(meter_ids_for_type) != 1:
            return SAEReadingTypeActivity(
                status="not_available", note="Multiple current meters require review."
            )

        meter_id = meter_ids_for_type[0]
        reading = latest_readings.get((meter_id, row.tubewell_id, meter_type))
        reactivated_on = reactivation_dates.get(row.tubewell_id)
        if reading is None or (
            reactivated_on is not None and reading.reading_date < reactivated_on
        ):
            return SAEReadingTypeActivity(
                status="not_started", meter_id=meter_id,
                note="No applicable reading after registration/reactivation."
            )

        days_since = (today - reading.reading_date).days
        if days_since < 0:
            return SAEReadingTypeActivity(
                status="not_available", meter_id=meter_id,
                note="Future reading date needs verification."
            )
        return SAEReadingTypeActivity(
            status="overdue" if days_since >= MISSING_READING_WARNING_DAYS else "up_to_date",
            meter_id=meter_id,
            latest_reading_date=reading.reading_date,
            days_since_last_reading=days_since,
            # Do not expose another team's historical collector identity.
            collected_by_field_visitor=(
                row.field_user_name
                if reading.collected_by_user_id == row.field_user_id else None
            ),
        )

    items = []
    energy_overdue = prepaid_overdue = distinct_overdue = 0
    for row in assignments:
        energy = activity_for(row, "energy")
        prepaid = activity_for(row, "prepaid")
        energy_overdue += int(energy.status == "overdue")
        prepaid_overdue += int(prepaid.status == "overdue")
        distinct_overdue += int(energy.status == "overdue" or prepaid.status == "overdue")
        items.append(SAEReadingTubewellActivity(
            tubewell_id=row.tubewell_id,
            tubewell_number=row.tubewell_number,
            tubewell_name=row.tubewell_name,
            tubewell_is_active=row.tubewell_is_active,
            field_user_id=row.field_user_id,
            field_user_name=row.field_user_name,
            energy=energy,
            prepaid=prepaid,
        ))

    return SAEReadingActivityResponse(
        supervisor_id=current_user.id,
        management_unit_id=unit_id,
        warning_threshold_days=MISSING_READING_WARNING_DAYS,
        total_assigned_tubewells=len(items),
        energy_overdue=energy_overdue,
        prepaid_overdue=prepaid_overdue,
        overdue_tubewells=distinct_overdue,
        tubewells=items,
    )
