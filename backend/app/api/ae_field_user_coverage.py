# BMDA AE Field User Assignment Coverage
# Read-only, authenticated, management-unit scoped.

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.tubewell import Tubewell
from app.models.tubewell_assignment import TubewellAssignment


router = APIRouter(
    prefix="/dashboard/ae",
    tags=["AE Dashboard"],
)


class FieldUserCoverageItem(BaseModel):
    field_user_id: int
    full_name: str
    is_active: bool
    assigned_tubewells: int
    coverage_percentage: float


class AEFieldUserCoverageResponse(BaseModel):
    management_unit_id: int
    total_tubewells: int
    assigned_tubewells: int
    unassigned_tubewells: int
    unmatched_assignments: int
    field_users: list[FieldUserCoverageItem]


@router.get(
    "/field-user-coverage",
    response_model=AEFieldUserCoverageResponse,
)
def get_ae_field_user_coverage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "assistant_engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assistant Engineer access is required.",
        )

    unit_id = current_user.upazila_id

    if unit_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Management unit assignment is required.",
        )

    total_tubewells = db.scalar(
        select(func.count(Tubewell.id)).where(
            Tubewell.management_unit_id == unit_id
        )
    ) or 0

    assignment_counts = (
        select(
            TubewellAssignment.field_user_id.label("field_user_id"),
            func.count(
                func.distinct(TubewellAssignment.tubewell_id)
            ).label("assigned_count"),
        )
        .join(
            Tubewell,
            Tubewell.id == TubewellAssignment.tubewell_id,
        )
        .where(
            Tubewell.management_unit_id == unit_id,
            TubewellAssignment.ended_at.is_(None),
        )
        .group_by(TubewellAssignment.field_user_id)
        .subquery()
    )

    statement = (
        select(
            User.id,
            User.full_name,
            User.is_active,
            func.coalesce(
                assignment_counts.c.assigned_count, 0
            ),
        )
        .outerjoin(
            assignment_counts,
            assignment_counts.c.field_user_id == User.id,
        )
        .where(
            User.role == "field_user",
            User.upazila_id == unit_id,
        )
        .order_by(User.full_name.asc(), User.id.asc())
    )

    rows = db.execute(statement).all()

    field_users = []
    assigned_total = 0

    for user_id, full_name, is_active, assigned_count in rows:
        assigned_count = int(assigned_count)
        assigned_total += assigned_count

        percentage = (
            round(assigned_count * 100 / total_tubewells, 2)
            if total_tubewells > 0
            else 0.0
        )

        field_users.append(
            FieldUserCoverageItem(
                field_user_id=user_id,
                full_name=full_name,
                is_active=is_active,
                assigned_tubewells=assigned_count,
                coverage_percentage=percentage,
            )
        )

    # Count current assignments directly from authorized
    # tubewells, including assignments whose user record
    # is outside the expected unit or role.
    assigned_tubewells = db.scalar(
        select(
            func.count(
                func.distinct(TubewellAssignment.tubewell_id)
            )
        )
        .join(
            Tubewell,
            Tubewell.id == TubewellAssignment.tubewell_id,
        )
        .where(
            Tubewell.management_unit_id == unit_id,
            TubewellAssignment.ended_at.is_(None),
        )
    ) or 0

    return AEFieldUserCoverageResponse(
        management_unit_id=unit_id,
        total_tubewells=total_tubewells,
        assigned_tubewells=assigned_tubewells,
        unassigned_tubewells=max(
            total_tubewells - assigned_tubewells, 0
        ),
        unmatched_assignments=max(assigned_tubewells - assigned_total, 0),
        field_users=field_users,
    )