
# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 2: FIELD USER CREATE REQUEST
# ============================================================

class MeterReplacementCreateRequest(BaseModel):

    tubewell_id: int = Field(
        gt=0,
    )

    old_meter_id: int = Field(
        gt=0,
    )

    new_meter_number: str = Field(
        min_length=1,
        max_length=100,
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )


# ============================================================
# SECTION 3: SAE REVIEW REQUEST
#
# "approved" means SAE recommendation only.
# It does not activate the replacement meter.
# ============================================================

class MeterReplacementReviewRequest(BaseModel):

    action: Literal[
        "approved",
        "rejected",
    ]

    review_comment: str | None = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# SECTION 4: AE FINAL REVIEW REQUEST
#
# Only AE final approval may complete replacement.
# ============================================================

class MeterReplacementAEReviewRequest(BaseModel):

    action: Literal[
        "approved",
        "rejected",
    ]

    review_comment: str | None = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# SECTION 5: METER REPLACEMENT RESPONSE
# ============================================================

class MeterReplacementResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    # --------------------------------------------------------
    # 5.1 REQUEST IDENTIFICATION
    # --------------------------------------------------------

    id: int

    tubewell_id: int

    old_meter_id: int

    requested_by_user_id: int

    # Meter type is derived from the old meter, not trusted
    # from a client-provided type.
    meter_type: Literal["energy", "prepaid"]

    # --------------------------------------------------------
    # 5.2 REQUEST DETAILS
    # --------------------------------------------------------

    new_meter_number: str

    reason: str

    status: Literal[
        "pending",
        "pending_ae_approval",
        "approved",
        "rejected",
    ]

    requested_at: datetime

    # --------------------------------------------------------
    # 5.3 SAE REVIEW INFORMATION
    # --------------------------------------------------------

    reviewed_by_user_id: int | None

    reviewed_at: datetime | None

    review_comment: str | None

    # --------------------------------------------------------
    # 5.4 AE FINAL REVIEW INFORMATION
    # --------------------------------------------------------

    ae_reviewed_by_user_id: int | None

    ae_reviewed_at: datetime | None

    ae_review_comment: str | None

    # --------------------------------------------------------
    # 5.5 REPLACEMENT METER
    #
    # Must remain NULL until AE final approval.
    # --------------------------------------------------------

    new_meter_id: int | None
