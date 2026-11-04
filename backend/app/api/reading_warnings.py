# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.api.auth import get_current_user

from app.core.field_warning_management import (
    get_field_user_missing_reading_warnings,
)

from app.core.roles import UserRole

from app.db.database import get_db

from app.models.user import User

from app.schemas.reading_warning import (
    MissingReadingWarningResponse,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/reading-warnings",
    tags=["Reading Warnings"],
)


# ============================================================
# SECTION 3: FIELD USER REQUIREMENT
# ============================================================

def require_field_user(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:

    if (
        current_user.role
        != UserRole.FIELD_USER.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Field User access required.",
        )

    return current_user


# ============================================================
# SECTION 4: FIELD USER WARNING LIST
# ============================================================

@router.get(
    "/my",
    response_model=list[
        MissingReadingWarningResponse
    ],
)
def list_my_missing_reading_warnings(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        return (
            get_field_user_missing_reading_warnings(
                db,
                field_user_id=current_user.id,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )