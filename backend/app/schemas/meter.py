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
# SECTION 2: METER CREATE REQUEST
# Basic meter information currently supported by the model.
# ============================================================

class MeterCreateRequest(BaseModel):

    tubewell_id: int = Field(
        gt=0
    )

    meter_number: str | None = Field(
        default=None,
        max_length=100,
    )

    installed_at: date | None = None
    removed_at: date | None = None


# ============================================================
# SECTION 3: METER RESPONSE
# Safe meter information returned by the API.
# ============================================================

class MeterResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tubewell_id: int
    meter_number: str | None
    installed_at: date | None
    removed_at: date | None