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

from app.core.pending_request_management import (
    get_combined_pending_requests,
)

from app.core.roles import UserRole

from app.db.database import get_db

from app.models.user import User

from app.schemas.pending_request import (
    PendingRequestResponse,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/pending-requests",
    tags=["Pending Requests"],
)


# ============================================================
# SECTION 3: SUPERVISOR REQUIREMENT
# ============================================================

def require_supervisor(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:

    if (
        current_user.role
        != UserRole.SUPERVISOR.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor access required.",
        )

    return current_user


# ============================================================
# SECTION 4: COMBINED PENDING REQUEST QUEUE
# ============================================================

@router.get(
    "",
    response_model=list[PendingRequestResponse],
)
def list_combined_pending_requests(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    try:
        return get_combined_pending_requests(
            db,
            supervisor_id=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )