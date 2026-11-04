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


class Union(Base):
    __tablename__ = "unions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    actual_upazila_id: Mapped[int] = mapped_column(
        ForeignKey("actual_upazilas.id"),
        nullable=False,
    )