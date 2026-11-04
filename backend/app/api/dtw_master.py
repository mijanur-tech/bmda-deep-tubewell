
# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.auth import require_admin
from app.core.tubewell_management import validate_actual_upazila
from app.db.database import get_db

from app.models.actual_upazila import ActualUpazila
from app.models.dtw_master import DtwMaster
from app.models.mouza import Mouza
from app.models.tubewell import Tubewell
from app.models.tubewell_assignment import TubewellAssignment
from app.models.union import Union
from app.models.upazila import Upazila
from app.models.user import User

from app.schemas.dtw_master import (
    DtwMasterCreateRequest,
    DtwMasterCorrectionRequest,
    DtwMasterResponse,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/dtw-master",
    tags=["DTW Master"],
)


# ============================================================
# SECTION 3: EXISTING MASTER LIST
# Preserved without changing its behavior.
# ============================================================

@router.get(
    "",
    response_model=list[DtwMasterResponse],
)
def list_dtw_master(
    mouza_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):

    query = select(DtwMaster)

    if mouza_id is not None:

        mouza = db.get(
            Mouza,
            mouza_id,
        )

        if mouza is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mouza not found.",
            )

        query = query.where(
            DtwMaster.mouza_id == mouza_id
        )

    return db.scalars(
        query.order_by(
            DtwMaster.dtw_number.asc()
        )
    ).all()


# ============================================================
# SECTION 4: EXISTING MASTER CREATE
# Preserved without changing its behavior.
# ============================================================

@router.post(
    "",
    response_model=DtwMasterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dtw_master(
    request: DtwMasterCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Add a DTW Master number for an existing Mouza; does not register a Tubewell."""

    number = request.dtw_number.strip()

    if not number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DTW Number cannot be empty.",
        )

    if len(number) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DTW Number must be 100 characters or fewer.",
        )

    if number != request.dtw_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DTW Number must not contain leading or trailing spaces.",
        )

    mouza = db.get(Mouza, request.mouza_id)

    if mouza is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mouza not found.",
        )

    existing = db.scalar(
        select(DtwMaster).where(
            DtwMaster.dtw_number == number
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DTW Number already exists in DTW Master.",
        )

    record = DtwMaster(
        dtw_number=number,
        mouza_id=request.mouza_id,
    )

    db.add(record)

    try:
        db.commit()
        db.refresh(record)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DTW Number already exists in DTW Master.",
        )

    return record


# ============================================================
# SECTION 4A: ADMIN DTW NUMBER SEARCH
# Read-only search across all Mouzas.
# ============================================================

@router.get("/search")
def search_dtw_master(
    dtw_number: str = Query(min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    number = dtw_number.strip()

    if not number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DTW Number cannot be empty.",
        )

    # Find the exact Master record.
    master = db.scalar(
        select(DtwMaster).where(
            DtwMaster.dtw_number == number
        )
    )

    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DTW Number not found in Master.",
        )

    # Resolve its current geographic location.
    location = db.execute(
        select(Mouza, Union, ActualUpazila, Upazila)
        .join(Union, Mouza.union_id == Union.id)
        .join(
            ActualUpazila,
            Union.actual_upazila_id == ActualUpazila.id,
        )
        .join(
            Upazila,
            ActualUpazila.management_unit_id == Upazila.id,
        )
        .where(Mouza.id == master.mouza_id)
    ).first()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Master location mapping is incomplete.",
        )

    mouza, union, actual_upazila, management_unit = location

    # Determine whether the number has been registered.
    registered = db.scalar(
        select(Tubewell.id).where(
            Tubewell.tubewell_number == master.dtw_number
        )
    ) is not None

    return {
        "id": master.id,
        "dtw_number": master.dtw_number,
        "mouza_id": master.mouza_id,
        "registered": registered,
        "current_location": (
            f"{management_unit.name} / "
            f"{actual_upazila.name} / "
            f"{union.name} / "
            f"{mouza.name}"
        ),
    }

# ============================================================
# SECTION 5: ADMIN MASTER CORRECTION
#
# Correct the location of an existing DTW Master record.
#
# Unregistered:
#   Update DTW Master only.
#
# Registered:
#   Update DTW Master and Tubewell together.
#
# Existing IDs, DTW Number, meters, readings and assignment
# history are preserved.
# ============================================================

@router.put(
    "/{master_id}/correction",
    response_model=DtwMasterResponse,
)
def correct_dtw_master(
    master_id: int,
    request: DtwMasterCorrectionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):

    # --------------------------------------------------------
    # CHECK 1: Lock the selected Master record.
    # --------------------------------------------------------

    master = db.scalar(
        select(DtwMaster)
        .where(DtwMaster.id == master_id)
        .with_for_update()
    )

    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DTW Master record not found.",
        )

    # --------------------------------------------------------
    # CHECK 2: Validate target Mouza and its Union.
    # --------------------------------------------------------

    target = db.execute(
        select(Mouza, Union, ActualUpazila)
        .join(Union, Mouza.union_id == Union.id)
        .join(
            ActualUpazila,
            Union.actual_upazila_id == ActualUpazila.id,
        )
        .where(Mouza.id == request.mouza_id)
    ).first()

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target Mouza or location mapping not found.",
        )

    mouza, union, actual_upazila = target

    # --------------------------------------------------------
    # CHECK 3: Validate management unit and geographic mapping.
    # --------------------------------------------------------

    management_unit = db.get(
        Upazila,
        request.management_unit_id,
    )

    if management_unit is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Management unit not found.",
        )

    if (
        actual_upazila.management_unit_id
        != request.management_unit_id
        or not validate_actual_upazila(
            request.management_unit_id,
            actual_upazila.name,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Actual Upazila does not belong to the selected management unit.",
        )

    # --------------------------------------------------------
    # CHECK 4: Find and lock registered Tubewell.
    # --------------------------------------------------------

    tubewell = db.scalar(
        select(Tubewell)
        .where(
            Tubewell.tubewell_number == master.dtw_number
        )
        .with_for_update()
    )

    # --------------------------------------------------------
    # CHECK 5: Prevent cross-unit assignment conflicts.
    # --------------------------------------------------------

    if (
        tubewell is not None
        and tubewell.management_unit_id
        != request.management_unit_id
    ):

        current_assignment = db.scalar(
            select(TubewellAssignment)
            .where(
                TubewellAssignment.tubewell_id == tubewell.id,
                TubewellAssignment.ended_at.is_(None),
            )
            .with_for_update()
        )

        if current_assignment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot change management unit while "
                    "the Tubewell has an active Field User assignment."
                ),
            )

    # --------------------------------------------------------
    # SECTION 6: APPLY CORRECTION
    # Changes are committed together.
    # --------------------------------------------------------

    master.mouza_id = mouza.id

    if tubewell is not None:
        tubewell.management_unit_id = request.management_unit_id
        tubewell.actual_upazila = actual_upazila.name
        tubewell.union_name = union.name
        tubewell.mouza = mouza.name

    # --------------------------------------------------------
    # SECTION 7: ATOMIC COMMIT
    # Roll back both records if a database conflict occurs.
    # --------------------------------------------------------

    try:
        db.commit()
        db.refresh(master)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DTW Master correction could not be saved.",
        )

    return master
