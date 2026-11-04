# ============================================================
# BMDA AE PERSONNEL SUMMARY — READ ONLY
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.ae_personnel_summary import (
    AEPersonnelSummaryResponse,
    PersonnelStatusCounts,
)


router = APIRouter(
    prefix="/dashboard/ae",
    tags=["AE Dashboard"],
)


@router.get(
    "/personnel-summary",
    response_model=AEPersonnelSummaryResponse,
)
def get_ae_personnel_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only Assistant Engineers may access this endpoint.
    if current_user.role != "assistant_engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assistant Engineer access is required.",
        )

    # Never accept a management unit ID from the client.
    unit_id = current_user.upazila_id

    if unit_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Management unit assignment is required.",
        )

    # Aggregate only users belonging to the authenticated
    # Assistant Engineer's own management unit.
    statement = (
        select(
            User.role,
            User.is_active,
            func.count(User.id),
        )
        .where(
            User.upazila_id == unit_id,
            User.role.in_(["supervisor", "field_user"]),
        )
        .group_by(User.role, User.is_active)
    )

    rows = db.execute(statement).all()

    counts = {
        "supervisor": {
            "active": 0,
            "inactive": 0,
        },
        "field_user": {
            "active": 0,
            "inactive": 0,
        },
    }

    for role, is_active, count in rows:
        key = "active" if is_active else "inactive"
        counts[role][key] = count

    def build_counts(role: str) -> PersonnelStatusCounts:
        active = counts[role]["active"]
        inactive = counts[role]["inactive"]

        return PersonnelStatusCounts(
            total=active + inactive,
            active=active,
            inactive=inactive,
        )

    return AEPersonnelSummaryResponse(
        management_unit_id=unit_id,
        sub_assistant_engineers=build_counts("supervisor"),
        field_visitors=build_counts("field_user"),
    )
