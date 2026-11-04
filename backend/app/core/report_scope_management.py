# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from sqlalchemy import select
from sqlalchemy.sql import ColumnElement

from app.core.roles import UserRole

from app.models.reading import Reading
from app.models.tubewell import Tubewell
from app.models.user import User


# ============================================================
# SECTION 2: VALIDATE REPORT USER
# ============================================================

def validate_report_user(
    current_user: User,
) -> None:

    if current_user is None:
        raise ValueError(
            "Authenticated user is required."
        )

    if not current_user.is_active:
        raise ValueError(
            "Inactive user cannot access reports."
        )

    valid_roles = {
        UserRole.ADMIN.value,
        UserRole.ASSISTANT_ENGINEER.value,
        UserRole.SUPERVISOR.value,
        UserRole.FIELD_USER.value,
    }

    if current_user.role not in valid_roles:
        raise ValueError(
            "User role is not authorized for reports."
        )


# ============================================================
# SECTION 3: BUILD REPORT SCOPE CONDITION
# ============================================================

def get_report_scope_condition(
    current_user: User,
) -> ColumnElement[bool] | None:

    validate_report_user(
        current_user
    )

    # --------------------------------------------------------
    # ADMIN - GLOBAL ACCESS
    # --------------------------------------------------------

    if (
        current_user.role
        == UserRole.ADMIN.value
    ):
        return None

    # --------------------------------------------------------
    # ASSISTANT ENGINEER - OWN MANAGEMENT UNIT
    # --------------------------------------------------------

    if (
        current_user.role
        == UserRole.ASSISTANT_ENGINEER.value
    ):

        if current_user.upazila_id is None:
            raise ValueError(
                "Assistant Engineer has no management unit."
            )

        return (
            Tubewell.management_unit_id
            == current_user.upazila_id
        )

    # --------------------------------------------------------
    # SUPERVISOR - DIRECT FIELD USERS
    # --------------------------------------------------------

    if (
        current_user.role
        == UserRole.SUPERVISOR.value
    ):

        subordinate_ids = (
            select(User.id)
            .where(
                User.role
                == UserRole.FIELD_USER.value,

                User.supervisor_id
                == current_user.id,
            )
        )

        return (
            Reading.collected_by_user_id.in_(
                subordinate_ids
            )
        )

    # --------------------------------------------------------
    # FIELD USER - OWN READINGS
    # --------------------------------------------------------

    if (
        current_user.role
        == UserRole.FIELD_USER.value
    ):

        return (
            Reading.collected_by_user_id
            == current_user.id
        )

    raise ValueError(
        "Unsupported report role."
    )