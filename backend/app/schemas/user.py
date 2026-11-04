# ============================================================
# SECTION 1: IMPORTS
# Import datetime, Literal, and Pydantic tools.
# ============================================================

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 2: USER CREATION REQUEST
# Admin can create the three subordinate BMDA roles.
#
# Admin account creation is deliberately not exposed here.
# ============================================================

class UserCreateRequest(BaseModel):

    full_name: str = Field(
        min_length=1,
        max_length=150,
    )

    username: str = Field(
        min_length=1,
        max_length=100,
    )

    password: str = Field(
        min_length=1,
    )

    role: Literal[
        "assistant_engineer",
        "supervisor",
        "field_user",
    ]

    upazila_id: int = Field(
        gt=0
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


# ============================================================
# SECTION 3: USER UPDATE REQUEST
# Allow an Admin to correct an existing user's name
# and username without changing account identity.
#
# Role, management unit, reporting officer, password,
# and account status cannot be changed here.
# ============================================================

class UserUpdateRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    full_name: str = Field(
        min_length=1,
        max_length=150,
    )

    username: str = Field(
        min_length=1,
        max_length=100,
    )


# ============================================================
# SECTION 4: USER RESPONSE
# Safe account information returned by the API.
# Password hashes are never exposed.
# ============================================================

class UserResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    full_name: str
    username: str
    role: str
    upazila_id: int | None
    supervisor_id: int | None
    is_active: bool
    created_at: datetime


# ============================================================
# SECTION 5: MANAGEMENT UNIT RESPONSE
# Safe read-only management unit information.
# ============================================================

class ManagementUnitResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
