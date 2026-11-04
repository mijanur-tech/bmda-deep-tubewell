# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from typing import Literal

from pydantic import BaseModel


# ============================================================
# SECTION 2: STRUCTURED SYNC ERROR DETAIL
# ============================================================

class ReadingSyncErrorDetail(BaseModel):

    error_code: str

    message: str

    message_bn: str

    retryable: bool

    needs_attention: bool


# ============================================================
# SECTION 3: FASTAPI HTTP ERROR WRAPPER
#
# FastAPI HTTPException serializes custom detail under:
#
# {
#     "detail": {
#         ...
#     }
# }
# ============================================================

class ReadingSyncErrorResponse(BaseModel):

    detail: ReadingSyncErrorDetail


# ============================================================
# SECTION 4: DOCUMENTED ERROR CODES
# ============================================================

ReadingSyncErrorCode = Literal[
    "temporary_server_failure",
    "client_submission_conflict",
    "reading_date_invalid",
    "zero_confirmation_required",
    "prepaid_data_invalid",
    "reading_data_invalid",
    "reading_access_denied",
    "unknown_reading_rejection",
]