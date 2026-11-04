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

class TubewellStatusCreateRequest(BaseModel):

    tubewell_id: int = Field(
        gt=0,
    )

    requested_status: Literal[
        "active",
        "inactive",
    ]

    reason: str = Field(
        min_length=1,
        max_length=500,
    )


# ============================================================
# SECTION 3: SUPERVISOR REVIEW REQUEST
# ============================================================

class TubewellStatusReviewRequest(BaseModel):

    action: Literal[
        "approved",
        "rejected",
    ]

    review_comment: str | None = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# SECTION 4: STATUS REQUEST RESPONSE
# ============================================================

class TubewellStatusResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    tubewell_id: int

    requested_by_user_id: int

    requested_status: Literal[
        "active",
        "inactive",
    ]

    reason: str

    status: Literal[
        "pending",
        "pending_ae_approval",
        "approved",
        "rejected",
    ]

    requested_at: datetime

    reviewed_by_user_id: int | None

    reviewed_at: datetime | None

    review_comment: str | None
    ae_reviewed_by_user_id: int | None = None
    ae_reviewed_at: datetime | None = None
    ae_review_comment: str | None = None

# AE uses the same action vocabulary as Supervisor.
class TubewellStatusAEReviewRequest(BaseModel):
    action: Literal["approved", "rejected"]
    review_comment: str | None = Field(default=None, max_length=500)
