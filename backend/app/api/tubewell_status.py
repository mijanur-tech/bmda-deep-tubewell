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
from app.models.tubewell import Tubewell
from sqlalchemy.orm import Session

from app.api.auth import get_current_user

from app.core.roles import UserRole

from app.core.tubewell_status_management import (
    create_tubewell_status_request,
    review_tubewell_status_request,
    review_tubewell_status_request_by_ae,
)

from app.db.database import get_db

from app.models.tubewell_status_request import (
    TubewellStatusRequest,
)

from app.models.user import User

from app.schemas.tubewell_status import (
    TubewellStatusCreateRequest,
    TubewellStatusReviewRequest,
    TubewellStatusResponse,
    TubewellStatusAEReviewRequest,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/tubewell-status-requests",
    tags=["Tubewell Status Requests"],
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
# SECTION 5: FIELD USER BUSINESS ERROR MAPPING
# ============================================================

def raise_tubewell_status_http_error(
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
        "pending tubewell status request"
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
# SECTION 6: SUPERVISOR REVIEW ERROR MAPPING
# ============================================================

def raise_tubewell_status_review_http_error(
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
            detail="Tubewell status request not found.",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


# ============================================================
# SECTION 7: FIELD USER OWN REQUEST LIST
# ============================================================

@router.get(
    "/my",
    response_model=list[TubewellStatusResponse],
)
def list_my_tubewell_status_requests(
    request_status: Literal[
        "pending",
        "pending_ae_approval",
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
        TubewellStatusRequest
    ).where(
        TubewellStatusRequest.requested_by_user_id
        == current_user.id
    )

    if request_status is not None:
        query = query.where(
            TubewellStatusRequest.status
            == request_status
        )

    query = query.order_by(
        TubewellStatusRequest.requested_at.desc(),
        TubewellStatusRequest.id.desc(),
    )

    return db.scalars(
        query
    ).all()


# ============================================================
# SECTION 8: SUPERVISOR PENDING REQUEST QUEUE
# ============================================================

@router.get(
    "/pending",
    response_model=list[TubewellStatusResponse],
)
def list_pending_tubewell_status_requests(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    query = (
        select(TubewellStatusRequest)
        .join(
            User,
            User.id
            == TubewellStatusRequest.requested_by_user_id,
        )
        .join(Tubewell, Tubewell.id == TubewellStatusRequest.tubewell_id)
        .where(
            TubewellStatusRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == current_user.id,

            User.upazila_id == current_user.upazila_id,
            Tubewell.management_unit_id == current_user.upazila_id,
        )
        .order_by(
            TubewellStatusRequest.requested_at.desc(),
            TubewellStatusRequest.id.desc(),
        )
    )

    return db.scalars(
        query
    ).all()


# ============================================================
# SECTION 9: SUPERVISOR PENDING REQUEST DETAIL
# ============================================================

@router.get(
    "/pending/{request_id}",
    response_model=TubewellStatusResponse,
)
def get_pending_tubewell_status_request(
    request_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell status request not found.",
        )

    request_record = db.scalar(
        select(
            TubewellStatusRequest
        )
        .join(
            User,
            User.id
            == TubewellStatusRequest.requested_by_user_id,
        )
        .join(Tubewell, Tubewell.id == TubewellStatusRequest.tubewell_id)
        .where(
            TubewellStatusRequest.id
            == request_id,

            TubewellStatusRequest.status
            == "pending",

            User.role
            == UserRole.FIELD_USER.value,

            User.supervisor_id
            == current_user.id,

            User.upazila_id == current_user.upazila_id,
            Tubewell.management_unit_id == current_user.upazila_id,
        )
    )

    if request_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell status request not found.",
        )

    return request_record


# ============================================================
# SECTION 10: SUPERVISOR REVIEW
# ============================================================

@router.post(
    "/pending/{request_id}/review",
    response_model=TubewellStatusResponse,
)
def review_pending_tubewell_status_request(
    request_id: int,
    request: TubewellStatusReviewRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    try:
        request_record = (
            review_tubewell_status_request(
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
        raise_tubewell_status_review_http_error(
            exc
        )

    return request_record


# ============================================================
# SECTION 11: FIELD USER OWN REQUEST DETAIL
# ============================================================

@router.get(
    "/my/{request_id}",
    response_model=TubewellStatusResponse,
)
def get_my_tubewell_status_request(
    request_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell status request not found.",
        )

    request_record = db.scalar(
        select(
            TubewellStatusRequest
        ).where(
            TubewellStatusRequest.id
            == request_id,

            TubewellStatusRequest.requested_by_user_id
            == current_user.id,
        )
    )

    if request_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell status request not found.",
        )

    return request_record


# ============================================================
# SECTION 12: CREATE STATUS REQUEST
# ============================================================

@router.post(
    "",
    response_model=TubewellStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_tubewell_status_request(
    request: TubewellStatusCreateRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        request_record = (
            create_tubewell_status_request(
                db,
                tubewell_id=(
                    request.tubewell_id
                ),
                field_user_id=(
                    current_user.id
                ),
                requested_status=(
                    request.requested_status
                ),
                reason=request.reason,
            )
        )

    except ValueError as exc:
        raise_tubewell_status_http_error(
            exc
        )

    return request_record

# ============================================================
# SECTION 13: AE FINAL APPROVAL QUEUE / REVIEW
# ============================================================

def require_assistant_engineer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ASSISTANT_ENGINEER.value or current_user.upazila_id is None:
        raise HTTPException(status_code=403, detail="Assistant Engineer access required.")
    return current_user


@router.get("/ae/pending", response_model=list[TubewellStatusResponse])
def list_ae_pending_status_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_assistant_engineer),
):
    from app.models.tubewell import Tubewell
    return db.scalars(
        select(TubewellStatusRequest)
        .join(Tubewell, Tubewell.id == TubewellStatusRequest.tubewell_id)
        .where(TubewellStatusRequest.status == "pending_ae_approval",
               Tubewell.management_unit_id == current_user.upazila_id)
        .order_by(TubewellStatusRequest.requested_at.desc())
    ).all()


@router.post("/ae/pending/{request_id}/review", response_model=TubewellStatusResponse)
def ae_final_review_status_request(
    request_id: int, request: TubewellStatusAEReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_assistant_engineer),
):
    try:
        return review_tubewell_status_request_by_ae(
            db, request_id=request_id, ae_id=current_user.id,
            action=request.action, review_comment=request.review_comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Request not found or not eligible for AE review.") from exc
