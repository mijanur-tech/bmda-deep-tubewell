# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


# ============================================================
# SECTION 2: COMBINED PENDING REQUEST RESPONSE
# ============================================================

class PendingRequestResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    request_type: Literal[
        "meter_replacement",
        "tubewell_status",
        "reading_correction",
    ]

    request_id: int

    tubewell_id: int

    reading_id: int | None = None

    requested_by_user_id: int

    reason: str

    status: Literal[
        "pending",
    ]

    requested_at: datetime

    # --------------------------------------------------------
    # Type-specific summary fields
    # --------------------------------------------------------

    requested_status: str | None = None

    old_meter_id: int | None = None

    new_meter_number: str | None = None

    reading_type: str | None = None