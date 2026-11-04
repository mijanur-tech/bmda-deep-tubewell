
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
    text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.user import Base


# ============================================================
# SECTION 2: METER REPLACEMENT REQUEST MODEL
# ============================================================

class MeterReplacementRequest(Base):

    __tablename__ = "meter_replacement_requests"

    # ========================================================
    # SECTION 3: DATABASE CONSTRAINTS
    # ========================================================

    __table_args__ = (
        CheckConstraint(
            "meter_type IN ('energy', 'prepaid')",
            name="ck_meter_replacement_meter_type",
        ),

        CheckConstraint(
            """
            status IN (
                'pending',
                'pending_ae_approval',
                'approved',
                'rejected'
            )
            """,
            name="ck_meter_replacement_status",
        ),

        CheckConstraint(
            """
            (
                status = 'pending'
                AND reviewed_by_user_id IS NULL
                AND reviewed_at IS NULL
                AND ae_reviewed_by_user_id IS NULL
                AND ae_reviewed_at IS NULL
                AND new_meter_id IS NULL
            )
            OR
            (
                status = 'pending_ae_approval'
                AND reviewed_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
                AND ae_reviewed_by_user_id IS NULL
                AND ae_reviewed_at IS NULL
                AND new_meter_id IS NULL
            )
            OR
            (
                status = 'approved'
                AND reviewed_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
                AND ae_reviewed_by_user_id IS NOT NULL
                AND ae_reviewed_at IS NOT NULL
                AND new_meter_id IS NOT NULL
            )
            OR
            (
                status = 'rejected'
                AND reviewed_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
                AND new_meter_id IS NULL
                AND (
                    (
                        ae_reviewed_by_user_id IS NULL
                        AND ae_reviewed_at IS NULL
                    )
                    OR
                    (
                        ae_reviewed_by_user_id IS NOT NULL
                        AND ae_reviewed_at IS NOT NULL
                    )
                )
            )
            """,
            name="ck_meter_replacement_review_state",
        ),

        Index(
            "ux_meter_replacement_pending_per_tubewell_type",
            "tubewell_id",
            "meter_type",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'pending_ae_approval')"
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
    # SECTION 6: OLD METER
    # ========================================================

    old_meter_id: Mapped[int] = mapped_column(
        ForeignKey("meters.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 7: REQUESTING FIELD USER
    # ========================================================

    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 7A: METER TYPE (ENERGY OR PREPAID)
    # Matches the applied 579a2d10f946 migration.
    # ========================================================

    meter_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # ========================================================
    # SECTION 8: PROPOSED NEW METER NUMBER
    # ========================================================

    new_meter_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ========================================================
    # SECTION 9: REPLACEMENT REASON
    # ========================================================

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # ========================================================
    # SECTION 10: REQUEST STATUS
    #
    # pending:
    #   Waiting for SAE review.
    #
    # pending_ae_approval:
    #   SAE recommended; waiting for AE decision.
    #
    # approved:
    #   AE approved; meter replacement completed.
    #
    # rejected:
    #   SAE or AE rejected the request.
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # ========================================================
    # SECTION 11: REQUEST TIME
    # ========================================================

    requested_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # ========================================================
    # SECTION 12: SAE REVIEW
    #
    # Existing columns are preserved.
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

    # ========================================================
    # SECTION 13: AE FINAL REVIEW
    #
    # New columns for Assistant Engineer decisions.
    # ========================================================

    ae_reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    ae_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ae_review_comment: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ========================================================
    # SECTION 14: CREATED REPLACEMENT METER
    #
    # Must remain NULL until AE final approval.
    # ========================================================

    new_meter_id: Mapped[int | None] = mapped_column(
        ForeignKey("meters.id"),
        nullable=True,
    )
