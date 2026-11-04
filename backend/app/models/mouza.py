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


class Mouza(Base):
    __tablename__ = "mouzas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    union_id: Mapped[int] = mapped_column(
        ForeignKey("unions.id"),
        nullable=False,
    )