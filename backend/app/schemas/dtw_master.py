from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 1: DTW MASTER RESPONSE
# Existing API response - unchanged.
# ============================================================

class DtwMasterResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    dtw_number: str
    mouza_id: int


# ============================================================
# SECTION 2: DTW MASTER CREATE REQUEST
# Existing create API - unchanged.
# ============================================================

class DtwMasterCreateRequest(BaseModel):
    # New master numbers must be assigned to an existing Mouza.
    dtw_number: str
    mouza_id: int


# ============================================================
# SECTION 3: ADMIN MASTER CORRECTION REQUEST
# Correct location without changing the permanent DTW Number.
#
# Actual Upazila and Union will be determined from the
# selected Mouza in the database.
# ============================================================

class DtwMasterCorrectionRequest(BaseModel):
    mouza_id: int = Field(gt=0)
    management_unit_id: int = Field(gt=0)
