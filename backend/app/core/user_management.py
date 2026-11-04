# ============================================================
# SECTION 1: IMPORTS
# Import database tools and existing BMDA models.
# ============================================================

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.upazila import Upazila

from app.core.roles import (
    UserRole,
    validate_upazila_assignment,
    validate_supervisor_assignment,
)


# ============================================================
# SECTION 2: ASSISTANT ENGINEER VALIDATION
# Check whether an Assistant Engineer can be assigned
# to a management unit under an Admin.
#
# This function does not create or modify any user.
# ============================================================

def validate_assistant_engineer_creation(
    db: Session,
    upazila_id: int,
    admin_id: int,
) -> bool:

    # CHECK 1: Validate the management unit ID.
    if not validate_upazila_assignment(
        UserRole.ASSISTANT_ENGINEER.value,
        upazila_id,
    ):
        return False

    # CHECK 2: Confirm the management unit exists.
    unit = db.get(Upazila, upazila_id)

    if unit is None:
        return False

    # CHECK 3: Find the reporting Admin.
    if (
        not isinstance(admin_id, int)
        or isinstance(admin_id, bool)
        or admin_id <= 0
    ):
        return False

    admin = db.get(User, admin_id)

    if admin is None:
        return False

    if not admin.is_active:
        return False

    # CHECK 4: Validate the reporting hierarchy.
    if not validate_supervisor_assignment(
        UserRole.ASSISTANT_ENGINEER.value,
        admin.role,
    ):
        return False

    if admin.upazila_id is not None:
        return False

    # CHECK 5: Prevent duplicate Assistant Engineers.
    existing_engineer = db.scalar(
        select(User.id).where(
            User.role == UserRole.ASSISTANT_ENGINEER.value,
            User.upazila_id == upazila_id,
        )
    )

    if existing_engineer is not None:
        return False

    return True


# ============================================================
# SECTION 3: USERNAME AVAILABILITY VALIDATION
# Check username format and availability.
#
# True  = Valid username and available.
# False = Invalid username or already used.
#
# Username comparisons are case-insensitive.
# ============================================================

def is_username_available(
    db: Session,
    username: str,
) -> bool:

    # CHECK 1: Reject non-text input.
    if not isinstance(username, str):
        return False

    # CHECK 2: Reject empty or whitespace-only usernames.
    if not username.strip():
        return False

    # CHECK 3: Maximum length is 100 characters.
    if len(username) > 100:
        return False

    # CHECK 4: Reject leading or trailing whitespace.
    if username != username.strip():
        return False

    # CHECK 5: Case-insensitive database lookup.
    existing_user_id = db.scalar(
        select(User.id).where(
            func.lower(User.username) == username.lower()
        )
    )

    return existing_user_id is None


# ============================================================
# SECTION 4: FULL NAME VALIDATION
# Check the full name before creating a user account.
#
# True  = Full name is valid.
# False = Full name is invalid.
# ============================================================

def validate_full_name(
    full_name: str,
) -> bool:

    # CHECK 1: Reject non-text input.
    if not isinstance(full_name, str):
        return False

    # CHECK 2: Reject empty or whitespace-only names.
    if not full_name.strip():
        return False

    # CHECK 3: Maximum length is 150 characters.
    if len(full_name) > 150:
        return False

    return True


# ============================================================
# SECTION 5: SUPERVISOR CREATION VALIDATION
# Check whether a Supervisor can be assigned to
# an Assistant Engineer in a management unit.
#
# True  = All validation rules passed.
# False = One or more rules failed.
#
# This function does NOT create or modify users.
# ============================================================

def validate_supervisor_creation(
    db: Session,
    upazila_id: int,
    assistant_engineer_id: int,
) -> bool:

    # CHECK 1: Validate the management unit ID.
    if (
        not isinstance(upazila_id, int)
        or isinstance(upazila_id, bool)
        or upazila_id <= 0
    ):
        return False

    if not validate_upazila_assignment(
        UserRole.SUPERVISOR.value,
        upazila_id,
    ):
        return False

    # CHECK 2: Confirm the management unit exists.
    unit = db.get(Upazila, upazila_id)

    if unit is None:
        return False

    # CHECK 3: Validate the Assistant Engineer ID.
    if (
        not isinstance(assistant_engineer_id, int)
        or isinstance(assistant_engineer_id, bool)
        or assistant_engineer_id <= 0
    ):
        return False

    # CHECK 4: Confirm the Assistant Engineer exists.
    assistant = db.get(User, assistant_engineer_id)

    if assistant is None:
        return False

    # CHECK 5: Assistant Engineer must be active.
    if not assistant.is_active:
        return False

    # CHECK 6: Validate the reporting hierarchy.
    if not validate_supervisor_assignment(
        UserRole.SUPERVISOR.value,
        assistant.role,
    ):
        return False

    # CHECK 7: Both users must belong to the same unit.
    if assistant.upazila_id != upazila_id:
        return False

    # CHECK 8: Maximum two Supervisors per Assistant Engineer.
    # Count both active and inactive accounts.
    supervisor_count = db.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.SUPERVISOR.value,
            User.supervisor_id == assistant_engineer_id,
        )
    )

    if supervisor_count >= 2:
        return False

    return True


# ============================================================
# SECTION 6: FIELD USER CREATION VALIDATION
# Check whether a Field User can be assigned to
# a Supervisor in the same management unit.
#
# No fixed numerical limit on Field Users per Supervisor.
#
# True  = All validation rules passed.
# False = One or more rules failed.
#
# This function does NOT create or modify users.
# ============================================================

def validate_field_user_creation(
    db: Session,
    upazila_id: int,
    supervisor_id: int,
) -> bool:

    # --------------------------------------------------------
    # CHECK 1: Validate the management unit ID.
    # --------------------------------------------------------

    if (
        not isinstance(upazila_id, int)
        or isinstance(upazila_id, bool)
        or upazila_id <= 0
    ):
        return False

    if not validate_upazila_assignment(
        UserRole.FIELD_USER.value,
        upazila_id,
    ):
        return False

    # --------------------------------------------------------
    # CHECK 2: Confirm the management unit exists.
    # --------------------------------------------------------

    unit = db.get(Upazila, upazila_id)

    if unit is None:
        return False

    # --------------------------------------------------------
    # CHECK 3: Validate the Supervisor ID.
    # --------------------------------------------------------

    if (
        not isinstance(supervisor_id, int)
        or isinstance(supervisor_id, bool)
        or supervisor_id <= 0
    ):
        return False

    # --------------------------------------------------------
    # CHECK 4: Confirm the Supervisor exists.
    # --------------------------------------------------------

    supervisor = db.get(User, supervisor_id)

    if supervisor is None:
        return False

    # --------------------------------------------------------
    # CHECK 5: Supervisor must be active.
    # --------------------------------------------------------

    if not supervisor.is_active:
        return False

    # --------------------------------------------------------
    # CHECK 6: Validate the reporting hierarchy.
    # A Field User must report to a Supervisor.
    # --------------------------------------------------------

    if not validate_supervisor_assignment(
        UserRole.FIELD_USER.value,
        supervisor.role,
    ):
        return False

    # --------------------------------------------------------
    # CHECK 7: Both users must belong to the same unit.
    # --------------------------------------------------------

    if supervisor.upazila_id != upazila_id:
        return False

    # --------------------------------------------------------
    # RESULT: All validation rules passed.
    # No numerical Field User limit is applied.
    # No database changes are made here.
    # --------------------------------------------------------

    return True