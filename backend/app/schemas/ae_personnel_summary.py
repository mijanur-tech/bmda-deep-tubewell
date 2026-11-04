from pydantic import BaseModel, Field


# ============================================================
# SECTION 1: PERSONNEL STATUS COUNTS
# Read-only aggregate counts for one personnel role.
# ============================================================

class PersonnelStatusCounts(BaseModel):
    total: int = Field(ge=0)
    active: int = Field(ge=0)
    inactive: int = Field(ge=0)


# ============================================================
# SECTION 2: AE PERSONNEL SUMMARY RESPONSE
# Only aggregate information for the authenticated AE's
# own management unit. No personal user data is exposed.
# ============================================================

class AEPersonnelSummaryResponse(BaseModel):
    management_unit_id: int = Field(gt=0)
    sub_assistant_engineers: PersonnelStatusCounts
    field_visitors: PersonnelStatusCounts
