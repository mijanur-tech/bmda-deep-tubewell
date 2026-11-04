# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.user import Base


# ============================================================
# SECTION 2: READING CORRECTION REQUEST MODEL
# ============================================================

class ReadingCorrectionRequest(Base):

    __tablename__ = "reading_correction_requests"

    # ========================================================
    # SECTION 3: DATABASE CONSTRAINTS
    # ========================================================

    __table_args__ = (
        CheckConstraint(
            """
            status IN (
                'pending',
                'approved',
                'rejected'
            )
            """,
            name="ck_reading_correction_status",
        ),

        CheckConstraint(
            """
            (
                status = 'pending'
                AND reviewed_by_user_id IS NULL
                AND reviewed_at IS NULL
            )
            OR
            (
                status IN (
                    'approved',
                    'rejected'
                )
                AND reviewed_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
            )
            """,
            name="ck_reading_correction_review_state",
        ),

        Index(
            "ux_reading_correction_one_pending_per_reading",
            "reading_id",
            unique=True,
            postgresql_where=text(
                "status = 'pending'"
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
    # SECTION 5: ORIGINAL SYNCED READING
    # ========================================================

    reading_id: Mapped[int] = mapped_column(
        ForeignKey("readings.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 6: REQUESTING FIELD USER
    # ========================================================

    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 7: PROPOSED CORRECTION PAYLOAD
    #
    # JSON text will be stored here.
    # Actual validation will depend on Energy/Prepaid type.
    # ========================================================

    correction_payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ========================================================
    # SECTION 8: CORRECTION REASON
    # ========================================================

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # ========================================================
    # SECTION 9: WORKFLOW STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # ========================================================
    # SECTION 10: REQUEST TIME
    # ========================================================

    requested_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP"
        ),
    )

    # ========================================================
    # SECTION 11: SUPERVISOR REVIEW
    # ========================================================

    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    review_comment: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )