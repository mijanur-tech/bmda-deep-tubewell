# ============================================================
# SECTION 1: IMPORTS
# Import FastAPI, SQLAlchemy, BMDA models, roles,
# and security tools.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)

from app.db.database import get_db
from app.models.user import User
from app.models.upazila import Upazila

from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)


# ============================================================
# SECTION 2: ROUTER CONFIGURATION
# All authentication endpoints start with /auth.
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# SECTION 3: BEARER TOKEN CONFIGURATION
# Read JWT tokens from the Authorization header.
# ============================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


# ============================================================
# SECTION 4: AUTHENTICATION ERROR
# Standard response for invalid authentication.
# ============================================================

def authentication_error() -> HTTPException:

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Invalid or expired authentication credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


# ============================================================
# SECTION 5: GET CURRENT USER
# Validate the JWT and load the active user from PostgreSQL.
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:

    if credentials is None:
        raise authentication_error()

    if credentials.scheme.lower() != "bearer":
        raise authentication_error()

    user_id = decode_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise authentication_error()

    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise authentication_error()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    return user


# ============================================================
# SECTION 6: REQUIRE ADMIN
# Allow only an active BMDA Admin to use an endpoint.
# ============================================================

def require_admin(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:

    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is required.",
        )

    return current_user


# ============================================================
# SECTION 7: LOGIN ENDPOINT
# Verify username/password and issue a JWT access token.
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):

    if request.username != request.username.strip():
        raise authentication_error()

    user = db.scalar(
        select(User).where(
            func.lower(User.username)
            == request.username.lower()
        )
    )

    if user is None:
        raise authentication_error()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise authentication_error()

    access_token = create_access_token(
        user.id
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


# ============================================================
# SECTION 8: CURRENT USER ENDPOINT
# Return safe information about the authenticated user.
# ============================================================

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # SECTION 1: Get only the logged-in user's unit.
    unit_name = None

    if current_user.upazila_id is not None:
        unit = db.get(Upazila, current_user.upazila_id)

        if unit is not None:
            unit_name = unit.name

    # SECTION 2: Return existing safe user fields
    # along with the assigned management unit name.
    response = CurrentUserResponse.model_validate(current_user)

    return response.model_copy(
        update={"upazila_name": unit_name}
    )