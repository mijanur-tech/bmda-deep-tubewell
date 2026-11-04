# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


# ============================================================
# SECTION 2: FIELD WARNING RESPONSE
#
# Supports:
# - Missing reading warnings
# - Inactive tubewell warnings
#
# Inactive tubewell status does NOT block reading submission.
# ============================================================

class MissingReadingWarningResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    tubewell_id: int

    meter_id: int | None = None

    warning_type: Literal[
        "missing_reading",
        "inactive_tubewell",
    ] = "missing_reading"

    reading_type: Literal[
        "energy",
        "prepaid",
    ] | None = None

    warning: bool

    days_since_last_reading: int | None = None

    latest_reading_date: date | None = None

    message: str | None = None