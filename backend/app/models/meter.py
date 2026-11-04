# ============================================================
# SECTION 1: IMPORTS
# Import Python date and SQLAlchemy database tools.
# ============================================================

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


# ============================================================
# SECTION 2: METER MODEL
# Store Energy and Prepaid meters separately.
#
# A tubewell can exist without a meter record.
# Multiple meter records preserve replacement history.
# ============================================================

class Meter(Base):

    __tablename__ = "meters"

    # ========================================================
    # SECTION 3: METER DATABASE ID
    # Unique ID for each meter record.
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ========================================================
    # SECTION 4: TUBEWELL RELATIONSHIP
    # Each meter belongs to an existing tubewell.
    #
    # The tubewell identity remains unchanged during
    # meter replacement.
    # ========================================================

    tubewell_id: Mapped[int] = mapped_column(
        ForeignKey("tubewells.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 5: METER TYPE
    # Distinguish Energy and Prepaid meters.
    #
    # Allowed values:
    # energy
    # prepaid
    #
    # Nullable temporarily for compatibility with the
    # approved database migration.
    # ========================================================

    meter_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # ========================================================
    # SECTION 6: METER NUMBER
    # Store the actual meter number when available.
    #
    # No fictional meter number is required.
    # ========================================================

    meter_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # SECTION 7: INSTALLATION DATE
    # Date when the meter was installed.
    #
    # This information may be entered later.
    # ========================================================

    installed_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ========================================================
    # SECTION 8: REMOVAL DATE
    # Date when the meter was removed or replaced.
    #
    # A blank value does not automatically prove that
    # the meter is currently installed.
    # ========================================================

    removed_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
