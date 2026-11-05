
# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ============================================================
# SECTION 2: ENERGY CORRECTION PAYLOAD
# ============================================================

class EnergyCorrectionPayload(BaseModel):

    reading_type: Literal[
        "energy"
    ] = "energy"

    previous_reading: Decimal

    current_reading: Decimal

    l1: Decimal

    l2: Decimal

    l3: Decimal

    zero_confirmed: bool = False


# ============================================================
# SECTION 3: PREPAID CORRECTION PAYLOAD
# ============================================================

class PrepaidCorrectionPayload(BaseModel):

    reading_type: Literal[
        "prepaid"
    ] = "prepaid"

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


# ============================================================
# SECTION 4: FIELD USER CREATE REQUEST
# ============================================================

class ReadingCorrectionCreateRequest(BaseModel):

    reading_id: int = Field(
        gt=0,
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )

    correction: (
        EnergyCorrectionPayload
        | PrepaidCorrectionPayload
    )


# ============================================================
# SECTION 5: SUPERVISOR REVIEW REQUEST
# ============================================================

class ReadingCorrectionReviewRequest(BaseModel):

    action: Literal[
        "approved",
        "rejected",
    ]

    review_comment: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_rejection_reason(self):

        # Approval does not require a comment.
        # Rejection must include a meaningful reason.

        if self.action == "rejected":

            if (
                self.review_comment is None
                or not self.review_comment.strip()
            ):
                raise ValueError(
                    "Rejection reason is required."
                )

        return self


# ============================================================
# SECTION 6: RESPONSE
# ============================================================

class ReadingCorrectionResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    reading_id: int

    requested_by_user_id: int

    correction_payload: str

    reason: str

    status: Literal[
        "pending",
        "approved",
        "rejected",
    ]

    requested_at: object

    reviewed_by_user_id: int | None

    reviewed_at: object | None

    review_comment: str | None
