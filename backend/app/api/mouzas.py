from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.db.database import get_db
from app.models.mouza import Mouza
from app.models.union import Union
from app.models.user import User
from app.schemas.mouza import MouzaCreateRequest, MouzaResponse

router = APIRouter(prefix="/mouzas", tags=["Mouzas"])


@router.get("", response_model=list[MouzaResponse])
def list_mouzas(
    union_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    query = select(Mouza)
    if union_id is not None:
        if db.get(Union, union_id) is None:
            raise HTTPException(status_code=400, detail="Union not found.")
        query = query.where(Mouza.union_id == union_id)
    return db.scalars(query.order_by(Mouza.name.asc())).all()


@router.post("", response_model=MouzaResponse, status_code=status.HTTP_201_CREATED)
def create_mouza(
    request: MouzaCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Create a Mouza under an existing Union."""
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Mouza name cannot be empty.")
    if name != request.name:
        raise HTTPException(
            status_code=400,
            detail="Mouza name must not contain leading or trailing spaces.",
        )
    union = db.get(Union, request.union_id)
    if union is None:
        raise HTTPException(status_code=400, detail="Union not found.")

    duplicate = db.scalar(
        select(Mouza).where(
            Mouza.union_id == request.union_id,
            func.lower(Mouza.name) == name.lower(),
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Mouza already exists in the selected Union.",
        )

    record = Mouza(name=name, union_id=request.union_id)
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mouza could not be saved because of a duplicate or database constraint.",
        )
    return record
