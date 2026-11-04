# ============================================================
# SECTION 1: IMPORTS
# Import Python date and SQLAlchemy database tools.
# ============================================================

from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.user import Base


# ============================================================
# SECTION 2: TUBEWELL ASSIGNMENT MODEL
# Store current and historical Field User assignments.
#
# Current assignment:
# ended_at is NULL
#
# Historical assignment:
# ended_at has a date
# ============================================================

class TubewellAssignment(Base):

    __tablename__ = "tubewell_assignments"

    # ========================================================
    # SECTION 3: DATABASE INDEXES
    # Only one current Field User assignment is allowed
    # for each tubewell.
    #
    # Historical rows remain preserved.
    # ========================================================

    __table_args__ = (
        Index(
            "ux_tubewell_assignments_one_current_per_tubewell",
            "tubewell_id",
            unique=True,
            postgresql_where=text(
                "ended_at IS NULL"
            ),
        ),
    )

    # ========================================================
    # SECTION 4: ASSIGNMENT ID
    # Unique database ID for each assignment record.
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ========================================================
    # SECTION 5: TUBEWELL ID
    # Identify the assigned deep tubewell.
    # ========================================================

    tubewell_id: Mapped[int] = mapped_column(
        ForeignKey("tubewells.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 6: FIELD USER ID
    # Identify the Field User receiving responsibility.
    #
    # Role and unit validation are handled in business logic.
    # ========================================================

    field_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 7: ASSIGNMENT START DATE
    # Store the assignment date when known.
    #
    # Do not invent missing dates.
    # ========================================================

    assigned_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ========================================================
    # SECTION 8: ASSIGNMENT END DATE
    # NULL means this is the current assignment.
    #
    # A date means this assignment has ended and remains
    # available as historical assignment information.
    # ========================================================

    ended_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )