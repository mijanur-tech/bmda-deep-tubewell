from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.db.database import get_db
from app.models.actual_upazila import ActualUpazila
from app.models.union import Union
from app.models.user import User
from app.schemas.union import UnionCreateRequest, UnionResponse

router = APIRouter(prefix="/unions", tags=["Unions"])


@router.get("", response_model=list[UnionResponse])
def list_unions(
    actual_upazila_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    query = select(Union)
    if actual_upazila_id is not None:
        actual_upazila = db.get(ActualUpazila, actual_upazila_id)
        if actual_upazila is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actual upazila not found.",
            )
        query = query.where(Union.actual_upazila_id == actual_upazila_id)
    return db.scalars(query.order_by(Union.name.asc())).all()


@router.post("", response_model=UnionResponse, status_code=status.HTTP_201_CREATED)
def create_union(
    request: UnionCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Create a Union under an existing Actual Upazila."""
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Union name cannot be empty.")
    if name != request.name:
        raise HTTPException(
            status_code=400,
            detail="Union name must not contain leading or trailing spaces.",
        )
    if db.get(ActualUpazila, request.actual_upazila_id) is None:
        raise HTTPException(status_code=400, detail="Actual upazila not found.")

    duplicate = db.scalar(
        select(Union).where(
            Union.actual_upazila_id == request.actual_upazila_id,
            func.lower(Union.name) == name.lower(),
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Union already exists in the selected Upazila.",
        )

    record = Union(name=name, actual_upazila_id=request.actual_upazila_id)
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Union could not be saved because of a duplicate or database constraint.",
        )
    return record
