# ============================================================
# BMDA TUBEWELL ASSIGNMENT API
#
# Executive Engineer (Admin):
#   Read-only access to all management units.
#
# Assistant Engineer:
#   Read/write access within own management unit.
#
# Supervisor / Field User:
#   No access to Assignment Management.
#
# Assignment history and business rules are preserved.
# ============================================================


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

from app.api.auth import get_current_user

from app.core.roles import UserRole

from app.core.tubewell_management import (
    assign_or_reassign_tubewell,
)

from app.db.database import get_db

from app.models.tubewell import Tubewell
from app.models.tubewell_assignment import TubewellAssignment
from app.models.user import User

from app.schemas.assignment import (
    AssignmentCreateRequest,
    AssignmentResponse,
    EligibleFieldUserResponse,
)


# ============================================================
# SECTION 2: ROUTER CONFIGURATION
# ============================================================

router = APIRouter(
    prefix="/assignments",
    tags=["Tubewell Assignments"],
)


# ============================================================
# SECTION 3: ASSIGNMENT READER AUTHORIZATION
#
# Admin:
#   Read all management units.
#
# Assistant Engineer:
#   Read own management unit only.
#
# Supervisor / Field User:
#   Access denied.
# ============================================================

def require_assignment_reader(
    current_user: User = Depends(get_current_user),
) -> User:

    if current_user.role == UserRole.ADMIN.value:
        return current_user

    if (
        current_user.role
        == UserRole.ASSISTANT_ENGINEER.value
    ):
        if current_user.upazila_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Assistant Engineer has no "
                    "assigned management unit."
                ),
            )

        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Assignment access is not permitted.",
    )


# ============================================================
# SECTION 4: MANAGEMENT UNIT ACCESS VALIDATION
#
# Admin:
#   May read any tubewell assignment.
#
# Assistant Engineer:
#   May access only tubewells belonging to own unit.
# ============================================================

def require_tubewell_unit_access(
    tubewell: Tubewell,
    current_user: User,
) -> None:

    if current_user.role == UserRole.ADMIN.value:
        return

    if (
        current_user.role
        == UserRole.ASSISTANT_ENGINEER.value
        and current_user.upazila_id is not None
        and current_user.upazila_id
        == tubewell.management_unit_id
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "You cannot access assignments "
            "outside your management unit."
        ),
    )


# ============================================================
# SECTION 5: LIST ASSIGNMENTS
#
# Admin:
#   All management units.
#
# Assistant Engineer:
#   Own management unit only.
#
# Existing optional filters are preserved.
# ============================================================

@router.get(
    "",
    response_model=list[AssignmentResponse],
)
def list_assignments(
    tubewell_id: int | None = Query(
        default=None,
        gt=0,
    ),
    field_user_id: int | None = Query(
        default=None,
        gt=0,
    ),
    current_only: bool = Query(
        default=False,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_assignment_reader
    ),
):

    query = select(TubewellAssignment)

    # Assistant Engineer: enforce server-side unit scope.

    if (
        current_user.role
        == UserRole.ASSISTANT_ENGINEER.value
    ):
        query = (
            query.join(
                Tubewell,
                Tubewell.id
                == TubewellAssignment.tubewell_id,
            )
            .where(
                Tubewell.management_unit_id
                == current_user.upazila_id
            )
        )

    if tubewell_id is not None:
        query = query.where(
            TubewellAssignment.tubewell_id
            == tubewell_id
        )

    if field_user_id is not None:
        query = query.where(
            TubewellAssignment.field_user_id
            == field_user_id
        )

    if current_only:
        query = query.where(
            TubewellAssignment.ended_at.is_(None)
        )

    assignments = db.scalars(
        query.order_by(
            TubewellAssignment.id.asc()
        )
    ).all()

    return assignments


# ============================================================
# SECTION 6: ELIGIBLE FIELD USERS
#
# GET /assignments/eligible-field-users
#
# Admin:
#   Can view active Field Users across all units.
#
# Assistant Engineer:
#   Can view active Field Users of own unit only.
#
# Supervisor / Field User:
#   Access denied.
#
# Only the following information is returned:
#   id
#   full_name
#   management_unit_id
#
# No username, password hash or other account information.
#
# This endpoint is READ-ONLY.
# ============================================================

@router.get(
    "/eligible-field-users",
    response_model=list[EligibleFieldUserResponse],
)
def list_eligible_field_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_assignment_reader
    ),
):

    # --------------------------------------------------------
    # CHECK 1: Active Field Users only.
    # --------------------------------------------------------

    query = select(User).where(
        User.role == UserRole.FIELD_USER.value,
        User.is_active.is_(True),
    )

    # --------------------------------------------------------
    # CHECK 2: Assistant Engineer's own management unit.
    #
    # This filter is enforced on the server.
    # Client-provided management unit selection cannot
    # expand the Assistant Engineer's access.
    # --------------------------------------------------------

    if (
        current_user.role
        == UserRole.ASSISTANT_ENGINEER.value
    ):
        query = query.where(
            User.upazila_id == current_user.upazila_id
        )

    # --------------------------------------------------------
    # CHECK 3: Load eligible accounts.
    # --------------------------------------------------------

    field_users = db.scalars(
        query.order_by(User.id.asc())
    ).all()

    # --------------------------------------------------------
    # CHECK 4: Return minimum required information.
    #
    # Explicitly map User.upazila_id to the response field
    # management_unit_id.
    # --------------------------------------------------------

    return [
        EligibleFieldUserResponse(
            id=user.id,
            full_name=user.full_name,
            management_unit_id=user.upazila_id,
        )
        for user in field_users
        if user.upazila_id is not None
    ]


# ============================================================
# SECTION 7: GET CURRENT ASSIGNMENT
#
# Admin:
#   Any management unit.
#
# Assistant Engineer:
#   Own management unit only.
# ============================================================

@router.get(
    "/current",
    response_model=AssignmentResponse | None,
)
def get_current_assignment(
    tubewell_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_assignment_reader
    ),
):

    tubewell = db.get(
        Tubewell,
        tubewell_id,
    )

    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    require_tubewell_unit_access(
        tubewell,
        current_user,
    )

    assignment = db.scalar(
        select(TubewellAssignment).where(
            TubewellAssignment.tubewell_id
            == tubewell_id,
            TubewellAssignment.ended_at.is_(None),
        )
    )

    return assignment


# ============================================================
# SECTION 8: GET ASSIGNMENT HISTORY
#
# Admin:
#   All management units.
#
# Assistant Engineer:
#   Own management unit only.
#
# Historical assignment records are not modified.
# ============================================================

@router.get(
    "/history/{tubewell_id}",
    response_model=list[AssignmentResponse],
)
def get_assignment_history(
    tubewell_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_assignment_reader
    ),
):

    if tubewell_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    tubewell = db.get(
        Tubewell,
        tubewell_id,
    )

    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    require_tubewell_unit_access(
        tubewell,
        current_user,
    )

    history = db.scalars(
        select(TubewellAssignment)
        .where(
            TubewellAssignment.tubewell_id
            == tubewell_id
        )
        .order_by(
            TubewellAssignment.id.asc()
        )
    ).all()

    return history


# ============================================================
# SECTION 9: CREATE OR REASSIGN TUBEWELL
#
# Assistant Engineer only.
#
# The selected tubewell must belong to the logged-in
# Assistant Engineer's management unit.
#
# Existing business logic validates:
#   - Field User role and active status
#   - Matching management unit
#   - Required reassignment date
#   - Current assignment and history
#   - Transaction and conflict handling
#
# Admin has no assignment write authority.
# ============================================================

@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_reassign_assignment(
    request: AssignmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # --------------------------------------------------------
    # CHECK 1: Only Assistant Engineers can write.
    # --------------------------------------------------------

    if (
        current_user.role
        != UserRole.ASSISTANT_ENGINEER.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only Assistant Engineers can "
                "create or change assignments."
            ),
        )

    # --------------------------------------------------------
    # CHECK 2: Assistant Engineer must have a unit.
    # --------------------------------------------------------

    if current_user.upazila_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Assistant Engineer has no "
                "assigned management unit."
            ),
        )

    # --------------------------------------------------------
    # CHECK 3: Tubewell must exist.
    # --------------------------------------------------------

    tubewell = db.get(
        Tubewell,
        request.tubewell_id,
    )

    if tubewell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tubewell not found.",
        )

    # --------------------------------------------------------
    # CHECK 4: Tubewell must belong to AE's unit.
    # --------------------------------------------------------

    if (
        tubewell.management_unit_id
        != current_user.upazila_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Cannot assign a tubewell "
                "outside your management unit."
            ),
        )

    # --------------------------------------------------------
    # CHECK 5: Existing business logic.
    # --------------------------------------------------------

    try:
        assignment = assign_or_reassign_tubewell(
            db,
            request.tubewell_id,
            request.field_user_id,
            request.assigned_at,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return assignment