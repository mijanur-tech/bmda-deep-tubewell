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


class DtwMaster(Base):
    __tablename__ = "dtw_master"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    dtw_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    mouza_id: Mapped[int] = mapped_column(
        ForeignKey("mouzas.id"),
        nullable=False,
    )