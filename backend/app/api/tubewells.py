# ============================================================
# SECTION 1: IMPORTS
# Import FastAPI, SQLAlchemy, BMDA auth, models, and schemas.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import (
    get_current_user,
    require_admin,
)

from app.core.roles import UserRole
from app.core.tubewell_management import (
    validate_actual_upazila,
)

from app.db.database import get_db
from app.models.tubewell import Tubewell
from app.models.upazila import Upazila
from app.models.user import User

from app.schemas.tubewell import (
    TubewellCreateRequest,
    TubewellUpdateRequest,
    TubewellStatusRequest,
    TubewellResponse,
)


# ============================================================
# SECTION 2: ROUTER CONFIGURATION
# ============================================================

router = APIRouter(
    prefix="/tubewells",
    tags=["Tubewells"],
)


# ============================================================
# SECTION 3: FIELD USER REQUIREMENT
# Only authenticated active Field Users may use My Tubewells.
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
# SECTION 3A: ROLE-SCOPED TUBEWELL READ ACCESS
# Admin: all units; AE and Supervisor: own management unit.
# ============================================================

def require_tubewell_reader(
    current_user: User = Depends(get_current_user),
) -> User:
    allowed_roles = {
        UserRole.ADMIN.value,
        UserRole.ASSISTANT_ENGINEER.value,
        UserRole.SUPERVISOR.value,
    }
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tubewell list/detail access denied.",
        )
    return current_user


def scoped_tubewells_query(current_user: User):
    query = select(Tubewell)
    if current_user.role == UserRole.ADMIN.value:
        return query
    if current_user.role == UserRole.ASSISTANT_ENGINEER.value:
        if current_user.upazila_id is None:
            return query.where(text("false"))
        return query.where(
            Tubewell.management_unit_id == current_user.upazila_id
        )
    if current_user.role == UserRole.SUPERVISOR.value:
        if current_user.upazila_id is None:
            return query.where(text("false"))
        return query.where(
            Tubewell.management_unit_id == current_user.upazila_id
        )
    return query.where(text("false"))


# ============================================================
# SECTION 4: FIELD USER - MY TUBEWELLS
# Return only currently assigned tubewells.
#
# Search:
# - DTW number
# - legacy tubewell name
# - actual upazila
# - union
# - mouza
# ============================================================

@router.get(
    "/my",
    response_model=list[TubewellResponse],
)
def list_my_tubewells(
    search: str | None = Query(
        default=None,
        max_length=150,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_field_user
    ),
):

    query = (
        select(Tubewell)
        .join(
            TubewellAssignment,
            TubewellAssignment.tubewell_id
            == Tubewell.id,
        )
        .where(
            TubewellAssignment.field_user_id
            == current_user.id,
            TubewellAssignment.ended_at.is_(
                None
            ),
        )
    )

    if search is not None:

        if not search.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search value cannot be empty.",
            )

        if search != search.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Search value must not contain "
                    "leading or trailing spaces."
                ),
            )

        normalized_search = (
            f"%{search.lower()}%"
        )

        query = query.where(
            or_(
                func.lower(
                    Tubewell.tubewell_number
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.name
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.actual_upazila
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.union_name
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.mouza
                ).like(
                    normalized_search
                ),
            )
        )

    return db.scalars(
        query.order_by(
            Tubewell.id.asc()
        )
    ).all()


# ============================================================
# SECTION 5: ADMIN - LIST TUBEWELLS
# ============================================================

@router.get(
    "",
    response_model=list[TubewellResponse],
)
def list_tubewells(
    search: str | None = Query(
        default=None,
        max_length=150,
    ),
    management_unit_id: int | None = Query(
        default=None,
        gt=0,
    ),
    actual_upazila: str | None = Query(
        default=None,
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_tubewell_reader
    ),
):

    query = scoped_tubewells_query(current_user)

    if search is not None:

        if not search.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search value cannot be empty.",
            )

        if search != search.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Search value must not contain "
                    "leading or trailing spaces."
                ),
            )

        normalized_search = (
            f"%{search.lower()}%"
        )

        query = query.where(
            or_(
                func.lower(
                    Tubewell.tubewell_number
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.name
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.actual_upazila
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.union_name
                ).like(
                    normalized_search
                ),
                func.lower(
                    Tubewell.mouza
                ).like(
                    normalized_search
                ),
            )
        )

    if management_unit_id is not None:

        management_unit = db.get(
            Upazila,
            management_unit_id,
        )

        if management_unit is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Management unit not found.",
            )

        query = query.where(
            Tubewell.management_unit_id
            == management_unit_id
        )

    if actual_upazila is not None:

        if not actual_upazila.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actual upazila cannot be empty.",
            )

        if actual_upazila != actual_upazila.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Actual upazila must not contain "
                    "leading or trailing spaces."
                ),
            )

        if management_unit_id is not None:

            if not validate_actual_upazila(
                management_unit_id,
                actual_upazila,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Actual upazila does not belong "
                        "to this management unit."
                    ),
                )

        query = query.where(
            Tubewell.actual_upazila
            == actual_upazila
        )

    return db.scalars(
        query.order_by(
            Tubewell.id.asc()
        )
    ).all()


# ============================================================
# SECTION 6: ADMIN - GET ONE TUBEWELL
# ============================================================

@router.get(
    "/{tubewell_id}",
    response_model=TubewellResponse,
)
def get_tubewell(
    tubewell_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_tubewell_reader
    ),
):

    tubewell = db.scalars(
        scoped_tubewells_query(current_user).where(
            Tubewell.id == tubewell_id
        )
    ).first()

    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    return tubewell


# ============================================================
# SECTION 7: ADMIN / SAE - CREATE TUBEWELL
# Admin: any management unit; SAE: own management unit only.
# AE and Field Visitors: forbidden.
# ============================================================

@router.post(
    "",
    response_model=TubewellResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tubewell(
    request: TubewellCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Authentication validates the user's active status.
    if current_user.role not in {
        UserRole.ADMIN.value,
        UserRole.SUPERVISOR.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Sub-Assistant Engineer access is required to register tubewells.",
        )

    # Enforce SAE scope on the server; never trust the browser's unit.
    # Admin is authorized to register across management units.
    if current_user.role == UserRole.SUPERVISOR.value and (
        current_user.upazila_id is None
        or request.management_unit_id != current_user.upazila_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tubewell registration is restricted to your management unit.",
        )

    # --------------------------------------------------------
    # CHECK 1: DTW number
    # --------------------------------------------------------

    if not request.tubewell_number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DTW number cannot be empty.",
        )

    if (
        request.tubewell_number
        != request.tubewell_number.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "DTW number must not contain "
                "leading or trailing spaces."
            ),
        )

    # --------------------------------------------------------
    # CHECK 2: Legacy tubewell name
    # Temporary until name field is fully removed.
    # --------------------------------------------------------

    if not request.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tubewell name cannot be empty.",
        )

    if request.name != request.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tubewell name must not contain "
                "leading or trailing spaces."
            ),
        )

    # --------------------------------------------------------
    # CHECK 3: Management Unit
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

    # --------------------------------------------------------
    # CHECK 4: Actual Upazila
    # --------------------------------------------------------

    if not request.actual_upazila.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Actual upazila cannot be empty.",
        )

    if (
        request.actual_upazila
        != request.actual_upazila.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Actual upazila must not contain "
                "leading or trailing spaces."
            ),
        )

    if not validate_actual_upazila(
        request.management_unit_id,
        request.actual_upazila,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Actual upazila does not belong "
                "to this management unit."
            ),
        )

    # --------------------------------------------------------
    # CHECK 5: Union
    # --------------------------------------------------------

    if not request.union_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Union cannot be empty.",
        )

    if (
        request.union_name
        != request.union_name.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Union must not contain "
                "leading or trailing spaces."
            ),
        )

    # --------------------------------------------------------
    # CHECK 6: Mouza
    # --------------------------------------------------------

    if not request.mouza.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mouza cannot be empty.",
        )

    if request.mouza != request.mouza.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Mouza must not contain "
                "leading or trailing spaces."
            ),
        )

    # --------------------------------------------------------
    # CHECK 7: Duplicate DTW number
    # --------------------------------------------------------

    existing = db.scalar(
        select(Tubewell).where(
            Tubewell.tubewell_number
            == request.tubewell_number
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DTW number already exists.",
        )

    # --------------------------------------------------------
    # CREATE TUBEWELL
    # --------------------------------------------------------

    tubewell = Tubewell(
        tubewell_number=request.tubewell_number,
        name=request.name,
        management_unit_id=(
            request.management_unit_id
        ),
        actual_upazila=request.actual_upazila,
        union_name=request.union_name,
        mouza=request.mouza,
    )

    db.add(
        tubewell
    )

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tubewell could not be created.",
        )

    db.refresh(
        tubewell
    )

    return tubewell

# ============================================================
# SECTION 8: ADMIN - EDIT TUBEWELL
# Check that number and location match the registered master.
# No records are removed or inserted during an edit.
# ============================================================

@router.put(
    "/{tubewell_id}",
    response_model=TubewellResponse,
)
def update_tubewell(
    tubewell_id: int,
    request: TubewellUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    tubewell = db.get(Tubewell, tubewell_id)
    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    # SECTION 8A: Validate all incoming text values.
    for field_name in (
        "tubewell_number",
        "name",
        "actual_upazila",
        "union_name",
        "mouza",
    ):
        value = getattr(request, field_name)
        if not value.strip() or value != value.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: empty or surrounding spaces.",
            )

    # SECTION 8B: Validate management unit and geographic upazila.
    if db.get(Upazila, request.management_unit_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Management unit not found.",
        )
    if not validate_actual_upazila(
        request.management_unit_id,
        request.actual_upazila,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Actual upazila does not belong to this management unit.",
        )

    # SECTION 8C: Check DTW master registration and linked location.
    # Only existing DTW master numbers at the correct Union/Mouza
    # can be selected. Master records are NOT changed by this API.
    master_location = db.execute(
        text("""
            SELECT m.name AS mouza_name, u.name AS union_name
            FROM dtw_master AS d
            JOIN mouzas AS m ON m.id = d.mouza_id
            JOIN unions AS u ON u.id = m.union_id
            WHERE d.dtw_number = :number
        """),
        {"number": request.tubewell_number},
    ).mappings().first()

    if master_location is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DTW number is not registered in DTW Master.",
        )
    if (
        master_location["mouza_name"] != request.mouza
        or master_location["union_name"] != request.union_name
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Union and Mouza must match the DTW Master record.",
        )

    # SECTION 8D: Prevent reusing another Tubewell's unique number.
    duplicate = db.scalar(
        select(Tubewell).where(
            Tubewell.tubewell_number == request.tubewell_number,
            Tubewell.id != tubewell_id,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DTW number already exists.",
        )

    # SECTION 8E: Save changes without changing status or history.
    tubewell.tubewell_number = request.tubewell_number
    tubewell.name = request.name
    tubewell.management_unit_id = request.management_unit_id
    tubewell.actual_upazila = request.actual_upazila
    tubewell.union_name = request.union_name
    tubewell.mouza = request.mouza

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tubewell could not be updated.",
        )
    db.refresh(tubewell)
    return tubewell


# ============================================================
# SECTION 9: ADMIN - DEACTIVATE / REACTIVATE TUBEWELL
# No DELETE endpoint: records and linked history remain intact.
# ============================================================

@router.patch(
    "/{tubewell_id}/status",
    response_model=TubewellResponse,
)
def change_tubewell_status(
    tubewell_id: int,
    request: TubewellStatusRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    tubewell = db.get(Tubewell, tubewell_id)
    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    tubewell.is_active = request.is_active
    db.commit()
    db.refresh(tubewell)
    return tubewell
