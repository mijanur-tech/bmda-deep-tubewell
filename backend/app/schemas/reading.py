# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 2: ENERGY READING REQUEST
# ============================================================

class EnergyReadingCreateRequest(BaseModel):

    tubewell_id: int = Field(gt=0)

    meter_id: int | None = Field(
        default=None,
        gt=0,
    )

    reading_date: date

    previous_reading: Decimal
    current_reading: Decimal

    l1: Decimal
    l2: Decimal
    l3: Decimal

    zero_confirmed: bool = False

    client_submission_id: str = Field(
        min_length=1,
        max_length=100,
    )


# ============================================================
# SECTION 3: PREPAID READING REQUEST
# ============================================================

class PrepaidReadingCreateRequest(BaseModel):

    tubewell_id: int = Field(gt=0)

    meter_id: int | None = Field(
        default=None,
        gt=0,
    )

    reading_date: date

    prepaid_meter_body_number: str = Field(
        min_length=1,
        max_length=100,
    )

    previous_reading: Decimal
    current_reading: Decimal

    previous_money: Decimal
    current_money: Decimal

    previous_time_minutes: int
    current_time_minutes: int

    client_submission_id: str = Field(
        min_length=1,
        max_length=100,
    )


# ============================================================
# SECTION 4: COMMON READING RESPONSE
# ============================================================

class ReadingBaseResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tubewell_id: int
    meter_id: int | None
    reading_date: date
    collected_by_user_id: int

    reading_type: Literal[
        "energy",
        "prepaid",
    ]

    previous_reading: Decimal
    current_reading: Decimal

    client_submission_id: str


# ============================================================
# SECTION 5: ENERGY RESPONSE
# ============================================================

class EnergyReadingResponse(
    ReadingBaseResponse
):

    reading_type: Literal["energy"]

    l1: Decimal
    l2: Decimal
    l3: Decimal

    zero_confirmed: bool

    difference: Decimal
    negative_difference: bool


# ============================================================
# SECTION 6: PREPAID RESPONSE
# ============================================================

class PrepaidReadingResponse(
    ReadingBaseResponse
):

    reading_type: Literal["prepaid"]

    prepaid_meter_body_number: str

    previous_money: Decimal
    current_money: Decimal
    money_difference: Decimal

    previous_time_minutes: int
    current_time_minutes: int

    time_difference_minutes: int
    time_difference_hours: Decimal

    reading_difference: Decimal

    negative_reading_difference: bool
    negative_money_difference: bool
    negative_time_difference: bool
    has_negative_difference: bool


# ============================================================
# SECTION 7: ADMIN READING LIST RESPONSE
# ============================================================

class ReadingListResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tubewell_id: int
    meter_id: int | None

    reading_date: date
    collected_by_user_id: int

    reading_type: Literal[
        "energy",
        "prepaid",
    ]

    previous_reading: Decimal
    current_reading: Decimal

    client_submission_id: str