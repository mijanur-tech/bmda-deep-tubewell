# ============================================================
# SECTION 1: IMPORTS
# Import datetime and Pydantic tools.
# ============================================================

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# SECTION 2: LOGIN REQUEST
# Data sent by a user when signing in.
# ============================================================

class LoginRequest(BaseModel):

    username: str = Field(
        min_length=1,
        max_length=100,
    )

    password: str = Field(
        min_length=1,
    )


# ============================================================
# SECTION 3: ACCESS TOKEN RESPONSE
# Returned after successful authentication.
# ============================================================

class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


# ============================================================
# SECTION 4: CURRENT USER RESPONSE
# Safe user information returned by authenticated endpoints.
#
# Password hashes are never included.
# ============================================================

class CurrentUserResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    full_name: str
    username: str
    role: str
    upazila_id: int | None
    upazila_name: str | None = None
    supervisor_id: int | None
    is_active: bool
    created_at: datetime