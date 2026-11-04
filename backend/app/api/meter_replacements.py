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

from app.core.meter_replacement_management import (
    create_meter_replacement_request,
    review_meter_replacement_request,
    review_meter_replacement_request_by_ae,
)

from app.core.roles import UserRole
from app.db.database import get_db

from app.models.meter_replacement_request import (
    MeterReplacementRequest,
)

from app.models.tubewell import Tubewell
from app.models.user import User

from app.schemas.meter_replacement import (
    MeterReplacementAEReviewRequest,
    MeterReplacementCreateRequest,
    MeterReplacementResponse,
    MeterReplacementReviewRequest,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/meter-replacements",
    tags=["Meter Replacements"],
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

def raise_meter_replacement_http_error(
    exc: ValueError,
) -> None:

    message = str(exc)

    if (
        "not authorized"
        in message.lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )

    if (
        "pending meter replacement request"
        in message.lower()
        and "already exists"
        in message.lower()
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
#
# Do not reveal whether an out-of-scope request exists.
# Not found, already reviewed, or outside Supervisor scope
# are all returned as 404.
# ============================================================

def raise_meter_replacement_review_http_error(
    exc: ValueError,
) -> None:

    message = str(exc)

    lowered = message.lower()

    if (
        "request not found" in lowered
        or (
            "supervisor is not authorized"
            in lowered
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
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
    response_model=list[MeterReplacementResponse],
)
def list_my_meter_replacement_requests(
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
        MeterReplacementRequest
    ).where(
        MeterReplacementRequest.requested_by_user_id
        == current_user.id
    )

    if request_status is not None:
        query = query.where(
            MeterReplacementRequest.status
            == request_status
        )

    query = query.order_by(
        MeterReplacementRequest.requested_at.desc(),
        MeterReplacementRequest.id.desc(),
    )

    return db.scalars(
        query
    ).all()


# ============================================================
# SECTION 8: SUPERVISOR PENDING REQUEST QUEUE
# ============================================================

@router.get(
    "/pending",
    response_model=list[MeterReplacementResponse],
)
def list_pending_meter_replacement_requests(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    query = (
        select(MeterReplacementRequest)
        .join(
            User,
            User.id
            == MeterReplacementRequest.requested_by_user_id,
        )
        .where(
            MeterReplacementRequest.status
            == "pending",

            User.supervisor_id
            == current_user.id,

            User.role
            == UserRole.FIELD_USER.value,
        )
        .order_by(
            MeterReplacementRequest.requested_at.desc(),
            MeterReplacementRequest.id.desc(),
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
    response_model=MeterReplacementResponse,
)
def get_pending_meter_replacement_request(
    request_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )

    replacement_request = db.scalar(
        select(
            MeterReplacementRequest
        )
        .join(
            User,
            User.id
            == MeterReplacementRequest.requested_by_user_id,
        )
        .where(
            MeterReplacementRequest.id
            == request_id,

            MeterReplacementRequest.status
            == "pending",

            User.supervisor_id
            == current_user.id,

            User.role
            == UserRole.FIELD_USER.value,
        )
    )

    if replacement_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )

    return replacement_request


# ============================================================
# SECTION 10: SUPERVISOR REVIEW REQUEST
#
# approved: forwards to AE; no meter record changes.
# rejected: closes request; no meter record changes.
# ============================================================

@router.post(
    "/pending/{request_id}/review",
    response_model=MeterReplacementResponse,
)
def review_pending_meter_replacement_request(
    request_id: int,
    request: MeterReplacementReviewRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_supervisor
    ),
):

    try:
        replacement_request = (
            review_meter_replacement_request(
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
        raise_meter_replacement_review_http_error(
            exc
        )

    return replacement_request


# ============================================================
# SECTION 11: FIELD USER OWN REQUEST DETAIL
# ============================================================

@router.get(
    "/my/{request_id}",
    response_model=MeterReplacementResponse,
)
def get_my_meter_replacement_request(
    request_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )

    replacement_request = db.scalar(
        select(
            MeterReplacementRequest
        ).where(
            MeterReplacementRequest.id
            == request_id,

            MeterReplacementRequest.requested_by_user_id
            == current_user.id,
        )
    )

    if replacement_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )

    return replacement_request


# ============================================================
# SECTION 12: CREATE METER REPLACEMENT REQUEST
# ============================================================

@router.post(
    "",
    response_model=MeterReplacementResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_meter_replacement_request(
    request: MeterReplacementCreateRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        replacement_request = (
            create_meter_replacement_request(
                db,
                tubewell_id=(
                    request.tubewell_id
                ),
                old_meter_id=(
                    request.old_meter_id
                ),
                field_user_id=(
                    current_user.id
                ),
                new_meter_number=(
                    request.new_meter_number
                ),
                reason=request.reason,
            )
        )

    except ValueError as exc:
        raise_meter_replacement_http_error(
            exc
        )

    return replacement_request

# ============================================================
# SECTION 13: AE ROLE REQUIREMENT
# ============================================================

def require_assistant_engineer(
    current_user: User = Depends(get_current_user),
) -> User:
    if (
        current_user.role != UserRole.ASSISTANT_ENGINEER.value
        or current_user.upazila_id is None
        or not current_user.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assistant Engineer access required.",
        )
    return current_user


# ============================================================
# SECTION 14: AE REVIEW ERROR MAPPING
# Hide existence of out-of-scope requests.
# ============================================================

def raise_ae_meter_replacement_review_http_error(exc: ValueError) -> None:
    message = str(exc)
    lowered = message.lower()
    if "not authorized" in lowered or "request not found" in lowered:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


# ============================================================
# SECTION 15: AE PENDING APPROVAL QUEUE
# ============================================================

@router.get(
    "/ae/pending",
    response_model=list[MeterReplacementResponse],
)
def list_ae_pending_meter_replacements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_assistant_engineer),
):
    query = (
        select(MeterReplacementRequest)
        .join(Tubewell, Tubewell.id == MeterReplacementRequest.tubewell_id)
        .where(
            MeterReplacementRequest.status == "pending_ae_approval",
            Tubewell.management_unit_id == current_user.upazila_id,
        )
        .order_by(
            MeterReplacementRequest.requested_at.desc(),
            MeterReplacementRequest.id.desc(),
        )
    )
    return db.scalars(query).all()


# ============================================================
# SECTION 16: AE PENDING APPROVAL DETAIL
# ============================================================

@router.get(
    "/ae/pending/{request_id}",
    response_model=MeterReplacementResponse,
)
def get_ae_pending_meter_replacement(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_assistant_engineer),
):
    if request_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )
    record = db.scalar(
        select(MeterReplacementRequest)
        .join(Tubewell, Tubewell.id == MeterReplacementRequest.tubewell_id)
        .where(
            MeterReplacementRequest.id == request_id,
            MeterReplacementRequest.status == "pending_ae_approval",
            Tubewell.management_unit_id == current_user.upazila_id,
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter replacement request not found.",
        )
    return record


# ============================================================
# SECTION 17: AE FINAL REVIEW
# Only this endpoint can finalize the replacement.
# ============================================================

@router.post(
    "/ae/pending/{request_id}/review",
    response_model=MeterReplacementResponse,
)
def review_ae_pending_meter_replacement(
    request_id: int,
    request: MeterReplacementAEReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_assistant_engineer),
):
    try:
        return review_meter_replacement_request_by_ae(
            db,
            request_id=request_id,
            ae_id=current_user.id,
            action=request.action,
            review_comment=request.review_comment,
        )
    except ValueError as exc:
        raise_ae_meter_replacement_review_http_error(exc)
