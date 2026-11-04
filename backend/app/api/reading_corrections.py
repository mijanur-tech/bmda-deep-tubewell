# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user

from app.core.reading_correction_management import (
    create_reading_correction_request,
    review_reading_correction_request,
)

from app.core.roles import UserRole
from app.db.database import get_db

from app.models.reading_correction_request import (
    ReadingCorrectionRequest,
)

from app.models.user import User

from app.schemas.reading_correction import (
    ReadingCorrectionCreateRequest,
    ReadingCorrectionResponse,
    ReadingCorrectionReviewRequest,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/reading-corrections",
    tags=["Reading Corrections"],
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
# SECTION 4: SUPERVISOR REQUIREMENT
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
# SECTION 5: CREATE ERROR MAPPING
# ============================================================

def raise_reading_correction_http_error(
    exc: ValueError,
) -> None:

    message = str(exc)
    lowered = message.lower()

    if "not authorized" in lowered:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )

    if (
        "pending reading correction request"
        in lowered
        and "already exists"
        in lowered
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


# ============================================================
# SECTION 6: REVIEW ERROR MAPPING
# ============================================================

def raise_reading_correction_review_http_error(
    exc: ValueError,
) -> None:

    message = str(exc)
    lowered = message.lower()

    if (
        "request not found" in lowered
        or "supervisor is not authorized" in lowered
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading correction request not found.",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


# ============================================================
# SECTION 7: FIELD USER OWN CORRECTION REQUEST LIST
# ============================================================

@router.get(
    "/my",
    response_model=list[ReadingCorrectionResponse],
)
def list_my_reading_corrections(
    request_status: Literal[
        "pending",
        "approved",
        "rejected",
    ] | None = Query(
        default=None,
        alias="status",
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    query = select(
        ReadingCorrectionRequest
    ).where(
        ReadingCorrectionRequest.requested_by_user_id
        == current_user.id
    )

    if request_status is not None:
        query = query.where(
            ReadingCorrectionRequest.status
            == request_status
        )

    query = query.order_by(
        ReadingCorrectionRequest.requested_at.desc(),
        ReadingCorrectionRequest.id.desc(),
    )

    return db.scalars(
        query
    ).all()


# ============================================================
# SECTION 8: SUPERVISOR PENDING CORRECTION QUEUE
# ============================================================

@router.get(
    "/pending",
    response_model=list[ReadingCorrectionResponse],
)
def list_pending_reading_corrections(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    query = (
        select(ReadingCorrectionRequest)
        .join(
            User,
            User.id
            == ReadingCorrectionRequest.requested_by_user_id,
        )
        .where(
            ReadingCorrectionRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == current_user.id,
        )
        .order_by(
            ReadingCorrectionRequest.requested_at.desc(),
            ReadingCorrectionRequest.id.desc(),
        )
    )

    return db.scalars(
        query
    ).all()


# ============================================================
# SECTION 9: SUPERVISOR PENDING CORRECTION DETAIL
# ============================================================

@router.get(
    "/pending/{request_id}",
    response_model=ReadingCorrectionResponse,
)
def get_pending_reading_correction(
    request_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading correction request not found.",
        )

    request_record = db.scalar(
        select(
            ReadingCorrectionRequest
        )
        .join(
            User,
            User.id
            == ReadingCorrectionRequest.requested_by_user_id,
        )
        .where(
            ReadingCorrectionRequest.id
            == request_id,

            ReadingCorrectionRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == current_user.id,
        )
    )

    if request_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading correction request not found.",
        )

    return request_record


# ============================================================
# SECTION 10: SUPERVISOR REVIEW CORRECTION
# ============================================================

@router.post(
    "/pending/{request_id}/review",
    response_model=ReadingCorrectionResponse,
)
def review_pending_reading_correction(
    request_id: int,
    request: ReadingCorrectionReviewRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    try:
        request_record = (
            review_reading_correction_request(
                db,
                request_id=request_id,
                supervisor_id=current_user.id,
                action=request.action,
                review_comment=(
                    request.review_comment
                ),
            )
        )

    except ValueError as exc:
        raise_reading_correction_review_http_error(
            exc
        )

    return request_record


# ============================================================
# SECTION 11: FIELD USER OWN CORRECTION DETAIL
# ============================================================

@router.get(
    "/my/{request_id}",
    response_model=ReadingCorrectionResponse,
)
def get_my_reading_correction(
    request_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading correction request not found.",
        )

    request_record = db.scalar(
        select(
            ReadingCorrectionRequest
        ).where(
            ReadingCorrectionRequest.id
            == request_id,

            ReadingCorrectionRequest.requested_by_user_id
            == current_user.id,
        )
    )

    if request_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading correction request not found.",
        )

    return request_record


# ============================================================
# SECTION 12: CREATE CORRECTION REQUEST
#
# Original Reading is NOT modified here.
# ============================================================

@router.post(
    "",
    response_model=ReadingCorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_reading_correction(
    request: ReadingCorrectionCreateRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        request_record = (
            create_reading_correction_request(
                db,
                reading_id=request.reading_id,
                field_user_id=current_user.id,
                correction=(
                    request.correction.model_dump()
                ),
                reason=request.reason,
            )
        )

    except ValueError as exc:
        raise_reading_correction_http_error(
            exc
        )

    return request_record