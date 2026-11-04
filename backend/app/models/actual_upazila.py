from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.user import Base


class ActualUpazila(Base):
    __tablename__ = "actual_upazilas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    management_unit_id: Mapped[int] = mapped_column(
        ForeignKey("upazilas.id"),
        nullable=False,
    )