# ============================================================
# SECTION 1: IMPORTS
# Pydantic tools for API request and response validation.
# ============================================================

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 2: TUBEWELL CREATE REQUEST
# Information required to register a new tubewell.
# ============================================================

class TubewellCreateRequest(BaseModel):

    tubewell_number: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str = Field(
        min_length=1,
    )

    management_unit_id: int = Field(
        gt=0,
    )

    actual_upazila: str = Field(
        min_length=1,
        max_length=100,
    )

    union_name: str = Field(
        min_length=1,
        max_length=100,
    )

    mouza: str = Field(
        min_length=1,
        max_length=150,
    )


# ============================================================
# SECTION 3: TUBEWELL UPDATE REQUEST
# Admin can correct existing tubewell information.
# The API will validate location and duplicate numbers.
# ============================================================

class TubewellUpdateRequest(TubewellCreateRequest):
    pass


# ============================================================
# SECTION 4: TUBEWELL STATUS REQUEST
# True  = Activate
# False = Deactivate
#
# Permanent Delete is not supported.
# ============================================================

class TubewellStatusRequest(BaseModel):

    is_active: bool


# ============================================================
# SECTION 5: TUBEWELL RESPONSE
# Return existing tubewell data and operational status.
# ============================================================

class TubewellResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    tubewell_number: str
    name: str
    management_unit_id: int
    actual_upazila: str
    union_name: str
    mouza: str
    is_active: bool


# ============================================================
# SECTION 2B: ATOMIC BULK CREATE REQUEST
# Accept a bounded list of normal Tubewell create requests.
# Existing individual create/edit schemas remain unchanged.
# ============================================================

class TubewellBulkCreateRequest(BaseModel):
    # Require between 1 and 500 items per batch.
    # Duplicate numbers and location matching will be checked
    # separately by the Bulk API before any commit.
    items: list[TubewellCreateRequest] = Field(
        min_length=1,
        max_length=500,
    )

