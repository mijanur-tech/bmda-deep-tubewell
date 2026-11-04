# ============================================================
# SECTION 1: IMPORTS
# Import FastAPI, SQLAlchemy, meter validation,
# models, and schemas.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.meter_management import (
    validate_meter_dates,
)

from app.db.database import get_db
from app.models.meter import Meter
from app.models.tubewell import Tubewell
from app.models.user import User

from app.schemas.meter import (
    MeterCreateRequest,
    MeterResponse,
)


# ============================================================
# SECTION 2: ROUTER CONFIGURATION
# Meter management endpoints start with /meters.
# ============================================================

router = APIRouter(
    prefix="/meters",
    tags=["Meter Management"],
)


# ============================================================
# SECTION 3: LIST METERS
# Admin can list meter records.
#
# Optional tubewell_id filter helps inspect meter history.
# ============================================================

@router.get(
    "",
    response_model=list[MeterResponse],
)
def list_meters(
    tubewell_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    query = select(Meter)

    if tubewell_id is not None:

        tubewell = db.get(
            Tubewell,
            tubewell_id,
        )

        if tubewell is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tubewell.",
            )

        query = query.where(
            Meter.tubewell_id == tubewell_id
        )

    meters = db.scalars(
        query.order_by(
            Meter.id.asc()
        )
    ).all()

    return meters


# ============================================================
# SECTION 4: GET SINGLE METER
# Admin can view one meter record.
# ============================================================

@router.get(
    "/{meter_id}",
    response_model=MeterResponse,
)
def get_meter(
    meter_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    if meter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter not found.",
        )

    meter = db.get(
        Meter,
        meter_id,
    )

    if meter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter not found.",
        )

    return meter


# ============================================================
# SECTION 5: CREATE METER
# Admin can create a basic meter record.
#
# This does NOT yet implement approved replacement workflow.
# ============================================================

@router.post(
    "",
    response_model=MeterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meter(
    request: MeterCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    # --------------------------------------------------------
    # CHECK 1: Confirm tubewell exists.
    # --------------------------------------------------------

    tubewell = db.get(
        Tubewell,
        request.tubewell_id,
    )

    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tubewell.",
        )

    # --------------------------------------------------------
    # CHECK 2: Validate optional meter number.
    # --------------------------------------------------------

    if request.meter_number is not None:

        if request.meter_number != request.meter_number.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter number.",
            )

        if not request.meter_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter number.",
            )

    # --------------------------------------------------------
    # CHECK 3: Validate installation/removal dates.
    # --------------------------------------------------------

    if not validate_meter_dates(
        request.installed_at,
        request.removed_at,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meter installation/removal dates.",
        )

    # --------------------------------------------------------
    # SECTION 6: CREATE DATABASE RECORD
    # --------------------------------------------------------

    new_meter = Meter(
        tubewell_id=request.tubewell_id,
        meter_number=request.meter_number,
        installed_at=request.installed_at,
        removed_at=request.removed_at,
    )

    db.add(
        new_meter
    )

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Meter could not be created because "
                "a database integrity rule was violated."
            ),
        )

    db.refresh(
        new_meter
    )

    return new_meter