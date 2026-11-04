
# ============================================================
# SECTION 1: IMPORTS
# Import Python date tools, SQLAlchemy database tools,
# BMDA models, and approved roles.
# ============================================================

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tubewell import Tubewell
from app.models.tubewell_assignment import TubewellAssignment

from app.core.roles import UserRole


# ============================================================
# SECTION 2: APPROVED MANAGEMENT UNIT MAPPING
# Each management unit has one or more actual upazilas.
# ============================================================

MANAGEMENT_UNIT_UPAZILAS = {
    1: ("Panchagarh", "Tetulia"),
    2: ("Boda",),
    3: ("Debiganj",),
    4: ("Atwari",),
}


# ============================================================
# SECTION 3: ACTUAL UPAZILA VALIDATION
# ============================================================

def validate_actual_upazila(
    management_unit_id: int,
    actual_upazila: str,
) -> bool:

    if (
        not isinstance(management_unit_id, int)
        or isinstance(management_unit_id, bool)
        or management_unit_id <= 0
    ):
        return False

    allowed_upazilas = MANAGEMENT_UNIT_UPAZILAS.get(
        management_unit_id
    )

    if allowed_upazilas is None:
        return False

    if not isinstance(actual_upazila, str):
        return False

    if not actual_upazila.strip():
        return False

    if actual_upazila != actual_upazila.strip():
        return False

    return actual_upazila in allowed_upazilas


# ============================================================
# SECTION 4: READING COLLECTOR VALIDATION
# Confirm that the collector is an active Field User.
# ============================================================

def validate_reading_collector(
    db: Session,
    collected_by_user_id: int,
) -> bool:

    if (
        not isinstance(collected_by_user_id, int)
        or isinstance(collected_by_user_id, bool)
        or collected_by_user_id <= 0
    ):
        return False

    user = db.get(
        User,
        collected_by_user_id,
    )

    if user is None:
        return False

    if user.role != UserRole.FIELD_USER.value:
        return False

    if not user.is_active:
        return False

    return True


# ============================================================
# SECTION 5: TUBEWELL ASSIGNMENT VALIDATION
#
# Check whether a Field User can be assigned to a tubewell.
#
# Approved safety policy:
# Inactive tubewells cannot receive new assignments
# or reassignments.
#
# Existing assignments and history are not changed.
#
# This function does not create an assignment.
# ============================================================

def validate_tubewell_assignment(
    db: Session,
    tubewell_id: int,
    field_user_id: int,
) -> bool:

    for record_id in (
        tubewell_id,
        field_user_id,
    ):
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id <= 0
        ):
            return False

    tubewell = db.get(
        Tubewell,
        tubewell_id,
    )

    if tubewell is None:
        return False

    # Inactive tubewells cannot receive assignments.
    if not tubewell.is_active:
        return False

    field_user = db.get(
        User,
        field_user_id,
    )

    if field_user is None:
        return False

    if field_user.role != UserRole.FIELD_USER.value:
        return False

    if not field_user.is_active:
        return False

    if (
        field_user.upazila_id
        != tubewell.management_unit_id
    ):
        return False

    return True


# ============================================================
# SECTION 6: ASSIGNMENT DATE VALIDATION
#
# Both dates may be unknown.
# An end date cannot exist before an assignment date.
# Datetime values are rejected.
#
# Existing validation behavior remains unchanged.
# ============================================================

def validate_assignment_dates(
    assigned_at: date | None,
    ended_at: date | None,
) -> bool:

    if assigned_at is not None:

        if not isinstance(
            assigned_at,
            date,
        ):
            return False

        if isinstance(
            assigned_at,
            datetime,
        ):
            return False

    if ended_at is not None:

        if not isinstance(
            ended_at,
            date,
        ):
            return False

        if isinstance(
            ended_at,
            datetime,
        ):
            return False

    if (
        assigned_at is None
        and ended_at is None
    ):
        return True

    if (
        assigned_at is None
        and ended_at is not None
    ):
        return False

    if ended_at is None:
        return True

    if ended_at < assigned_at:
        return False

    return True


# ============================================================
# SECTION 7: GET CURRENT ASSIGNMENT
#
# Current assignment means ended_at is NULL.
# ============================================================

def get_current_tubewell_assignment(
    db: Session,
    tubewell_id: int,
) -> TubewellAssignment | None:

    if (
        not isinstance(tubewell_id, int)
        or isinstance(tubewell_id, bool)
        or tubewell_id <= 0
    ):
        return None

    return db.scalar(
        select(TubewellAssignment).where(
            TubewellAssignment.tubewell_id
            == tubewell_id,
            TubewellAssignment.ended_at.is_(
                None
            ),
        )
    )


# ============================================================
# SECTION 8: CHECK CURRENT ASSIGNEE
# ============================================================

def is_current_tubewell_assignee(
    db: Session,
    tubewell_id: int,
    field_user_id: int,
) -> bool:

    current_assignment = (
        get_current_tubewell_assignment(
            db,
            tubewell_id,
        )
    )

    if current_assignment is None:
        return False

    return (
        current_assignment.field_user_id
        == field_user_id
    )


# ============================================================
# SECTION 9: ASSIGN OR REASSIGN TUBEWELL
#
# First assignment:
# assigned_at may be unknown.
#
# Reassignment:
# assigned_at is required.
#
# Previous assignment is preserved in history.
#
# New policy:
# Inactive tubewells cannot be assigned/reassigned.
# ============================================================

def assign_or_reassign_tubewell(
    db: Session,
    tubewell_id: int,
    field_user_id: int,
    assigned_at: date | None,
) -> TubewellAssignment:

    # --------------------------------------------------------
    # CHECK 1: Validate IDs.
    # --------------------------------------------------------

    for record_id in (
        tubewell_id,
        field_user_id,
    ):
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id <= 0
        ):
            raise ValueError(
                "Invalid tubewell or Field User ID."
            )

    # --------------------------------------------------------
    # CHECK 2: Validate assignment date type.
    # --------------------------------------------------------

    if not validate_assignment_dates(
        assigned_at,
        None,
    ):
        raise ValueError(
            "Invalid assignment date."
        )

    # --------------------------------------------------------
    # CHECK 3: Lock the tubewell row.
    # This serializes assignment changes for the tubewell.
    # --------------------------------------------------------

    tubewell = db.scalar(
        select(Tubewell)
        .where(
            Tubewell.id == tubewell_id
        )
        .with_for_update()
    )

    if tubewell is None:
        raise ValueError(
            "Tubewell not found."
        )

    # --------------------------------------------------------
    # CHECK 3A: Inactive tubewell protection.
    #
    # Check the locked database row before any modification.
    # This blocks BOTH first assignment and reassignment.
    #
    # Deactivation does not remove existing assignments.
    # --------------------------------------------------------

    if not tubewell.is_active:
        raise ValueError(
            "Cannot assign or reassign an inactive tubewell."
        )

    # --------------------------------------------------------
    # CHECK 4: Lock and validate the Field User.
    # --------------------------------------------------------

    field_user = db.scalar(
        select(User)
        .where(
            User.id == field_user_id
        )
        .with_for_update()
    )

    if field_user is None:
        raise ValueError(
            "Field User not found."
        )

    if field_user.role != UserRole.FIELD_USER.value:
        raise ValueError(
            "Selected user is not a Field User."
        )

    if not field_user.is_active:
        raise ValueError(
            "Selected Field User is inactive."
        )

    if (
        field_user.upazila_id
        != tubewell.management_unit_id
    ):
        raise ValueError(
            "Field User and tubewell must belong "
            "to the same management unit."
        )

    # --------------------------------------------------------
    # CHECK 5: Lock the current assignment, if one exists.
    # --------------------------------------------------------

    current_assignment = db.scalar(
        select(TubewellAssignment)
        .where(
            TubewellAssignment.tubewell_id
            == tubewell_id,
            TubewellAssignment.ended_at.is_(
                None
            ),
        )
        .with_for_update()
    )

    # --------------------------------------------------------
    # CHECK 6: Same current Field User means no reassignment.
    # Return the existing current assignment unchanged.
    # --------------------------------------------------------

    if (
        current_assignment is not None
        and current_assignment.field_user_id
        == field_user_id
    ):
        return current_assignment

    # --------------------------------------------------------
    # CHECK 7: Close old assignment during reassignment.
    # Never invent an effective reassignment date.
    # --------------------------------------------------------

    if current_assignment is not None:

        if assigned_at is None:
            raise ValueError(
                "Reassignment date is required."
            )

        if (
            current_assignment.assigned_at
            is not None
            and assigned_at
            < current_assignment.assigned_at
        ):
            raise ValueError(
                "Reassignment date cannot be before "
                "the current assignment date."
            )

        current_assignment.ended_at = (
            assigned_at
        )

    # --------------------------------------------------------
    # SECTION 10: CREATE NEW CURRENT ASSIGNMENT
    # ended_at remains NULL for the current assignment.
    # --------------------------------------------------------

    new_assignment = TubewellAssignment(
        tubewell_id=tubewell_id,
        field_user_id=field_user_id,
        assigned_at=assigned_at,
        ended_at=None,
    )

    db.add(
        new_assignment
    )

    # --------------------------------------------------------
    # SECTION 11: COMMIT ATOMIC TRANSACTION
    #
    # Database unique index provides final protection against
    # more than one current assignment per tubewell.
    # --------------------------------------------------------

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        raise ValueError(
            "Assignment conflict occurred. "
            "The tubewell may already have a "
            "current assignment."
        )

    db.refresh(
        new_assignment
    )

    return new_assignment
