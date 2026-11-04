
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class Upazila(Base):
    __tablename__ = "upazilas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )
