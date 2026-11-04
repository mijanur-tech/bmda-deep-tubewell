from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.db.database import get_db
from app.models.actual_upazila import ActualUpazila
from app.models.upazila import Upazila
from app.models.user import User
from app.schemas.actual_upazila import ActualUpazilaResponse


router = APIRouter(
    prefix="/actual-upazilas",
    tags=["Actual Upazilas"],
)


@router.get(
    "",
    response_model=list[ActualUpazilaResponse],
)
def list_actual_upazilas(
    management_unit_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):

    query = select(ActualUpazila)

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
            ActualUpazila.management_unit_id
            == management_unit_id
        )

    return db.scalars(
        query.order_by(
            ActualUpazila.id.asc()
        )
    ).all()