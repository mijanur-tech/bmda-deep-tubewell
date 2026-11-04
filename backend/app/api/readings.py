# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import (
    get_current_user,
    require_admin,
)

from app.core.reading_lookup import (
    get_latest_reading_for_field_user,
)

from app.core.reading_management import (
    create_energy_reading,
    create_prepaid_reading,
    validate_energy_reading,
    validate_prepaid_reading,
)

from app.core.reading_sync_error import (
    build_reading_sync_error,
    get_reading_sync_http_status,
)

from app.core.roles import UserRole

from app.db.database import get_db

from app.models.reading import Reading
from app.models.user import User

from app.schemas.reading import (
    EnergyReadingCreateRequest,
    EnergyReadingResponse,
    PrepaidReadingCreateRequest,
    PrepaidReadingResponse,
    ReadingListResponse,
)

from app.schemas.reading_sync_error import (
    ReadingSyncErrorResponse,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/readings",
    tags=["Readings"],
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
# SECTION 4: BUSINESS ERROR MAPPING
# ============================================================

def raise_reading_http_error(
    exc: ValueError,
) -> None:

    error_detail = (
        build_reading_sync_error(
            exc
        )
    )

    http_status = (
        get_reading_sync_http_status(
            error_detail
        )
    )

    raise HTTPException(
        status_code=http_status,
        detail=error_detail,
    )


# ============================================================
# SECTION 5: ENERGY RESPONSE BUILDER
# ============================================================

def build_energy_response(
    reading: Reading,
) -> EnergyReadingResponse:

    calculated = validate_energy_reading(
        previous_reading=reading.previous_reading,
        current_reading=reading.current_reading,
        l1=reading.l1,
        l2=reading.l2,
        l3=reading.l3,
        zero_confirmed=True,
    )

    return EnergyReadingResponse(
        id=reading.id,
        tubewell_id=reading.tubewell_id,
        meter_id=reading.meter_id,
        reading_date=reading.reading_date,

        collected_by_user_id=(
            reading.collected_by_user_id
        ),

        reading_type="energy",

        previous_reading=(
            reading.previous_reading
        ),

        current_reading=(
            reading.current_reading
        ),

        client_submission_id=(
            reading.client_submission_id
        ),

        l1=reading.l1,
        l2=reading.l2,
        l3=reading.l3,

        zero_confirmed=(
            reading.zero_confirmed
        ),

        difference=calculated[
            "difference"
        ],

        negative_difference=calculated[
            "negative_difference"
        ],
    )


# ============================================================
# SECTION 6: PREPAID RESPONSE BUILDER
# ============================================================

def build_prepaid_response(
    reading: Reading,
) -> PrepaidReadingResponse:

    calculated = validate_prepaid_reading(
        prepaid_meter_body_number=(
            reading.prepaid_meter_body_number
        ),

        previous_reading=(
            reading.previous_reading
        ),

        current_reading=(
            reading.current_reading
        ),

        previous_money=(
            reading.previous_money
        ),

        current_money=(
            reading.current_money
        ),

        previous_time_minutes=(
            reading.previous_time_minutes
        ),

        current_time_minutes=(
            reading.current_time_minutes
        ),
    )

    return PrepaidReadingResponse(
        id=reading.id,
        tubewell_id=reading.tubewell_id,
        meter_id=reading.meter_id,
        reading_date=reading.reading_date,

        collected_by_user_id=(
            reading.collected_by_user_id
        ),

        reading_type="prepaid",

        previous_reading=(
            reading.previous_reading
        ),

        current_reading=(
            reading.current_reading
        ),

        client_submission_id=(
            reading.client_submission_id
        ),

        prepaid_meter_body_number=(
            reading.prepaid_meter_body_number
        ),

        previous_money=(
            reading.previous_money
        ),

        current_money=(
            reading.current_money
        ),

        money_difference=calculated[
            "money_difference"
        ],

        previous_time_minutes=(
            reading.previous_time_minutes
        ),

        current_time_minutes=(
            reading.current_time_minutes
        ),

        time_difference_minutes=calculated[
            "time_difference_minutes"
        ],

        time_difference_hours=calculated[
            "time_difference_hours"
        ],

        reading_difference=calculated[
            "reading_difference"
        ],

        negative_reading_difference=calculated[
            "negative_reading_difference"
        ],

        negative_money_difference=calculated[
            "negative_money_difference"
        ],

        negative_time_difference=calculated[
            "negative_time_difference"
        ],

        has_negative_difference=calculated[
            "has_negative_difference"
        ],
    )


# ============================================================
# SECTION 7: TYPE-SPECIFIC RESPONSE DISPATCHER
# ============================================================

def build_reading_detail_response(
    reading: Reading,
) -> EnergyReadingResponse | PrepaidReadingResponse:

    if reading.reading_type == "energy":
        return build_energy_response(
            reading
        )

    if reading.reading_type == "prepaid":
        return build_prepaid_response(
            reading
        )

    raise ValueError(
        "Unsupported reading type."
    )


# ============================================================
# SECTION 8: FIELD USER OWN READING HISTORY
# ============================================================

@router.get(
    "/my",
    response_model=list[ReadingListResponse],
)
def list_my_readings(
    reading_type: Literal[
        "energy",
        "prepaid",
    ] | None = Query(default=None),

    tubewell_id: int | None = Query(
        default=None,
        gt=0,
    ),

    meter_id: int | None = Query(
        default=None,
        gt=0,
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    query = select(Reading).where(
        Reading.collected_by_user_id
        == current_user.id
    )

    if reading_type is not None:
        query = query.where(
            Reading.reading_type
            == reading_type
        )

    if tubewell_id is not None:
        query = query.where(
            Reading.tubewell_id
            == tubewell_id
        )

    if meter_id is not None:
        query = query.where(
            Reading.meter_id
            == meter_id
        )

    return db.scalars(
        query.order_by(
            Reading.reading_date.desc(),
            Reading.id.desc(),
        )
    ).all()


# ============================================================
# SECTION 9: FIELD USER LATEST TUBEWELL READING
#
# Access:
# Current assigned Field User only.
#
# History:
# Search all readings for the tubewell/meter, regardless of
# which Field User originally collected them.
# ============================================================

@router.get(
    "/my/latest",
    response_model=(
        EnergyReadingResponse
        | PrepaidReadingResponse
    ),
)
def get_my_latest_reading(
    tubewell_id: int = Query(
        ...,
        gt=0,
    ),

    reading_type: Literal[
        "energy",
        "prepaid",
    ] = Query(...),

    meter_id: int | None = Query(
        default=None,
        gt=0,
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        reading = (
            get_latest_reading_for_field_user(
                db,
                tubewell_id=tubewell_id,
                field_user_id=current_user.id,
                reading_type=reading_type,
                meter_id=meter_id,
            )
        )

    except ValueError as exc:

        message = str(exc)

        if (
            "not authorized"
            in message.lower()
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=message,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=message,
        )

    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No previous reading found.",
        )

    try:
        return build_reading_detail_response(
            reading
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        )


# ============================================================
# SECTION 10: FIELD USER OWN READING DETAIL
# ============================================================

@router.get(
    "/my/{reading_id}",
    response_model=(
        EnergyReadingResponse
        | PrepaidReadingResponse
    ),
)
def get_my_reading(
    reading_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    if reading_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found.",
        )

    reading = db.scalar(
        select(Reading).where(
            Reading.id == reading_id,

            Reading.collected_by_user_id
            == current_user.id,
        )
    )

    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found.",
        )

    try:
        return build_reading_detail_response(
            reading
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        )


# ============================================================
# SECTION 11: ADMIN READING LIST
# ============================================================

@router.get(
    "",
    response_model=list[ReadingListResponse],
)
def list_readings(
    reading_type: Literal[
        "energy",
        "prepaid",
    ] | None = Query(default=None),

    tubewell_id: int | None = Query(
        default=None,
        gt=0,
    ),

    meter_id: int | None = Query(
        default=None,
        gt=0,
    ),

    collected_by_user_id: int | None = Query(
        default=None,
        gt=0,
    ),

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_admin
    ),
):

    query = select(Reading)

    if reading_type is not None:
        query = query.where(
            Reading.reading_type
            == reading_type
        )

    if tubewell_id is not None:
        query = query.where(
            Reading.tubewell_id
            == tubewell_id
        )

    if meter_id is not None:
        query = query.where(
            Reading.meter_id
            == meter_id
        )

    if collected_by_user_id is not None:
        query = query.where(
            Reading.collected_by_user_id
            == collected_by_user_id
        )

    return db.scalars(
        query.order_by(
            Reading.id.asc()
        )
    ).all()


# ============================================================
# SECTION 12: ADMIN READING DETAIL
# ============================================================

@router.get(
    "/{reading_id}",
    response_model=(
        EnergyReadingResponse
        | PrepaidReadingResponse
    ),
)
def get_reading(
    reading_id: int,

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_admin
    ),
):

    if reading_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found.",
        )

    reading = db.get(
        Reading,
        reading_id,
    )

    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found.",
        )

    try:
        return build_reading_detail_response(
            reading
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        )


# ============================================================
# SECTION 13: ENERGY SUBMISSION
# ============================================================

@router.post(
    "/energy",
    response_model=EnergyReadingResponse,
    status_code=status.HTTP_201_CREATED,

    responses={
        400: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "Permanent reading validation rejection. "
                "The mobile client should move the item "
                "to Needs Attention."
            ),
        },

        403: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "The Field User is not permitted to "
                "submit the reading."
            ),
        },

        409: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "Client submission ID conflict. "
                "Automatic retry must stop."
            ),
        },

        503: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "Temporary server/database failure. "
                "The mobile client may retry later."
            ),
        },
    },
)
def submit_energy_reading(
    request: EnergyReadingCreateRequest,
    response: Response,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        reading, created = create_energy_reading(
            db,

            tubewell_id=(
                request.tubewell_id
            ),

            meter_id=request.meter_id,

            reading_date=(
                request.reading_date
            ),

            collected_by_user_id=(
                current_user.id
            ),

            previous_reading=(
                request.previous_reading
            ),

            current_reading=(
                request.current_reading
            ),

            l1=request.l1,
            l2=request.l2,
            l3=request.l3,

            zero_confirmed=(
                request.zero_confirmed
            ),

            client_submission_id=(
                request.client_submission_id
            ),
        )

    except ValueError as exc:
        raise_reading_http_error(
            exc
        )

    if not created:
        response.status_code = (
            status.HTTP_200_OK
        )

    return build_energy_response(
        reading
    )


# ============================================================
# SECTION 14: PREPAID SUBMISSION
# ============================================================

@router.post(
    "/prepaid",
    response_model=PrepaidReadingResponse,
    status_code=status.HTTP_201_CREATED,

    responses={
        400: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "Permanent reading validation rejection. "
                "The mobile client should move the item "
                "to Needs Attention."
            ),
        },

        403: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "The Field User is not permitted to "
                "submit the reading."
            ),
        },

        409: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "Client submission ID conflict. "
                "Automatic retry must stop."
            ),
        },

        503: {
            "model": ReadingSyncErrorResponse,
            "description": (
                "Temporary server/database failure. "
                "The mobile client may retry later."
            ),
        },
    },
)
def submit_prepaid_reading(
    request: PrepaidReadingCreateRequest,
    response: Response,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_field_user
    ),
):

    try:
        reading, created = create_prepaid_reading(
            db,

            tubewell_id=(
                request.tubewell_id
            ),

            meter_id=request.meter_id,

            reading_date=(
                request.reading_date
            ),

            collected_by_user_id=(
                current_user.id
            ),

            prepaid_meter_body_number=(
                request.prepaid_meter_body_number
            ),

            previous_reading=(
                request.previous_reading
            ),

            current_reading=(
                request.current_reading
            ),

            previous_money=(
                request.previous_money
            ),

            current_money=(
                request.current_money
            ),

            previous_time_minutes=(
                request.previous_time_minutes
            ),

            current_time_minutes=(
                request.current_time_minutes
            ),

            client_submission_id=(
                request.client_submission_id
            ),
        )

    except ValueError as exc:
        raise_reading_http_error(
            exc
        )

    if not created:
        response.status_code = (
            status.HTTP_200_OK
        )

    return build_prepaid_response(
        reading
    )