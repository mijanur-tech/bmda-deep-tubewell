
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    ASSISTANT_ENGINEER = "assistant_engineer"
    SUPERVISOR = "supervisor"
    FIELD_USER = "field_user"


def is_valid_role(role: str) -> bool:
    return role in UserRole._value2member_map_


def get_role_display_name(role: str) -> str:
    display_names = {
        UserRole.ADMIN: "Executive Engineer",
        UserRole.ASSISTANT_ENGINEER: "Assistant Engineer",
        UserRole.SUPERVISOR: "Sub-Assistant Engineer",
        UserRole.FIELD_USER: "Field Visitor",
    }

    if not is_valid_role(role):
        raise ValueError("Invalid user role")

    return display_names[UserRole(role)]


def validate_upazila_assignment(
    role: str,
    upazila_id: int | None,
) -> bool:
    if not is_valid_role(role):
        raise ValueError("Invalid user role")

    if role == UserRole.ADMIN:
        return upazila_id is None

    return (
        isinstance(upazila_id, int)
        and not isinstance(upazila_id, bool)
        and upazila_id > 0
    )


def validate_supervisor_assignment(
    user_role: str,
    supervisor_role: str | None,
) -> bool:
    if not is_valid_role(user_role):
        raise ValueError("Invalid user role")

    if supervisor_role is not None and not is_valid_role(
        supervisor_role
    ):
        raise ValueError("Invalid supervisor role")

    expected_supervisor_roles = {
        UserRole.ADMIN: None,
        UserRole.ASSISTANT_ENGINEER: UserRole.ADMIN,
        UserRole.SUPERVISOR: UserRole.ASSISTANT_ENGINEER,
        UserRole.FIELD_USER: UserRole.SUPERVISOR,
    }

    return (
        supervisor_role
        == expected_supervisor_roles[UserRole(user_role)]
    )


def validate_same_upazila(
    user_upazila_id: int | None,
    supervisor_upazila_id: int | None,
) -> bool:
    def valid_id(value: int | None) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        )

    return (
        valid_id(user_upazila_id)
        and valid_id(supervisor_upazila_id)
        and user_upazila_id == supervisor_upazila_id
    )
