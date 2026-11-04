# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.user import Base


# ============================================================
# SECTION 2: READING MODEL
# Store final Energy and Prepaid readings.
# ============================================================

class Reading(Base):

    __tablename__ = "readings"

    # ========================================================
    # SECTION 3: DATABASE CONSTRAINTS
    # ========================================================

    __table_args__ = (
        CheckConstraint(
            "reading_type IN ('energy', 'prepaid')",
            name="ck_readings_reading_type",
        ),

        CheckConstraint(
            """
            reading_type <> 'energy'
            OR (
                l1 IS NOT NULL
                AND l2 IS NOT NULL
                AND l3 IS NOT NULL
                AND zero_confirmed IS NOT NULL
            )
            """,
            name="ck_readings_energy_fields",
        ),

        CheckConstraint(
            """
            reading_type <> 'prepaid'
            OR (
                prepaid_meter_body_number IS NOT NULL
                AND previous_money IS NOT NULL
                AND current_money IS NOT NULL
                AND previous_time_minutes IS NOT NULL
                AND current_time_minutes IS NOT NULL
            )
            """,
            name="ck_readings_prepaid_fields",
        ),

        CheckConstraint(
            """
            (
                reading_type = 'energy'
                AND prepaid_meter_body_number IS NULL
                AND previous_money IS NULL
                AND current_money IS NULL
                AND previous_time_minutes IS NULL
                AND current_time_minutes IS NULL
            )
            OR
            (
                reading_type = 'prepaid'
                AND l1 IS NULL
                AND l2 IS NULL
                AND l3 IS NULL
                AND zero_confirmed IS NULL
            )
            """,
            name="ck_readings_type_specific_nulls",
        ),

        Index(
            "ux_readings_client_submission_id",
            "client_submission_id",
            unique=True,
            postgresql_where=text(
                "client_submission_id IS NOT NULL"
            ),
        ),
    )

    # ========================================================
    # SECTION 4: PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ========================================================
    # SECTION 5: TUBEWELL
    # ========================================================

    tubewell_id: Mapped[int] = mapped_column(
        ForeignKey("tubewells.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 6: METER
    # Optional when meter linkage is not known.
    # ========================================================

    meter_id: Mapped[int | None] = mapped_column(
        ForeignKey("meters.id"),
        nullable=True,
    )

    # ========================================================
    # SECTION 7: LEGACY GENERIC VALUE
    # Retained only for compatibility.
    # ========================================================

    reading_value: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    # ========================================================
    # SECTION 8: READING DATE
    # ========================================================

    reading_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ========================================================
    # SECTION 9: COLLECTOR
    # ========================================================

    collected_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 10: READING TYPE
    # Required final values:
    # energy
    # prepaid
    # ========================================================

    reading_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # ========================================================
    # SECTION 11: COMMON READING VALUES
    # Required for both Energy and Prepaid.
    # ========================================================

    previous_reading: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    current_reading: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    # ========================================================
    # SECTION 12: ENERGY FIELDS
    # Required only when reading_type = energy.
    # ========================================================

    l1: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    l2: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    l3: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    zero_confirmed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # ========================================================
    # SECTION 13: PREPAID FIELDS
    # Required only when reading_type = prepaid.
    # ========================================================

    prepaid_meter_body_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    previous_money: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    current_money: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    previous_time_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    current_time_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # SECTION 14: IDEMPOTENCY ID
    # Required for every final mobile submission.
    # ========================================================

    client_submission_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )