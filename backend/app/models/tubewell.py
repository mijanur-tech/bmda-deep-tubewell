# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.user import Base


# ============================================================
# SECTION 2: TUBEWELL MODEL
# ============================================================

class Tubewell(Base):

    __tablename__ = "tubewells"

    # ========================================================
    # SECTION 3: PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ========================================================
    # SECTION 4: PERMANENT DTW NUMBER
    # ========================================================

    tubewell_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    # ========================================================
    # SECTION 5: LEGACY TUBEWELL NAME
    # Temporary field.
    # Will be removed after the new location structure is stable.
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # ========================================================
    # SECTION 6: BMDA MANAGEMENT UNIT
    # ========================================================

    management_unit_id: Mapped[int] = mapped_column(
        ForeignKey("upazilas.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 7: ACTUAL GEOGRAPHIC UPAZILA
    # ========================================================

    actual_upazila: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ========================================================
    # SECTION 8: UNION
    # ========================================================

    union_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ========================================================
    # SECTION 9: MOUZA
    # ========================================================

    mouza: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # ========================================================
    # SECTION 10: CURRENT OPERATIONAL STATUS
    #
    # True  = Active
    # False = Inactive
    #
    # IMPORTANT:
    # Inactive status does NOT block reading submission.
    # Warning behavior will be handled separately.
    # ========================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )