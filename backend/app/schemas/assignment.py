# ============================================================
# SECTION 1: IMPORTS
# Import Python date and Pydantic tools.
# ============================================================

from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 2: ASSIGNMENT CREATE REQUEST
#
# Only Assistant Engineers may assign or reassign Field Users
# to tubewells within their own management unit.
#
# Authorization is enforced by the Assignment API.
# ============================================================

class AssignmentCreateRequest(BaseModel):

    tubewell_id: int = Field(
        gt=0
    )

    field_user_id: int = Field(
        gt=0
    )

    assigned_at: date | None = None


# ============================================================
# SECTION 3: ASSIGNMENT RESPONSE
# Safe assignment information returned by the API.
#
# Used for current assignments and assignment history.
# ============================================================

class AssignmentResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tubewell_id: int
    field_user_id: int
    assigned_at: date | None
    ended_at: date | None


# ============================================================
# SECTION 4: ELIGIBLE FIELD USER RESPONSE
#
# Provide only the information required for
# Tubewell Assignment Management.
#
# Admin:
#   Read-only visibility across all management units.
#
# Assistant Engineer:
#   Eligible Field Users from own management unit only.
#
# Supervisor / Field User:
#   No access.
#
# Username, password hash and other account details
# are deliberately excluded.
# ============================================================

class EligibleFieldUserResponse(BaseModel):

    id: int

    full_name: str

    management_unit_id: int