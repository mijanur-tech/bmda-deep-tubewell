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
# SECTION 2: TUBEWELL STATUS REQUEST MODEL
# ============================================================

class TubewellStatusRequest(Base):

    __tablename__ = "tubewell_status_requests"

    # ========================================================
    # SECTION 3: DATABASE CONSTRAINTS
    # ========================================================

    __table_args__ = (
        CheckConstraint(
            """
            requested_status IN (
                'active',
                'inactive'
            )
            """,
            name="ck_tubewell_status_requested_status",
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
            name="ck_tubewell_status_request_status",
        ),

        # Supervisor review is required before AE review. A Supervisor
        # rejection ends the request without an AE decision.
        CheckConstraint(
            """
            (
                status = 'pending'
                AND reviewed_by_user_id IS NULL
                AND reviewed_at IS NULL
                AND ae_reviewed_by_user_id IS NULL
                AND ae_reviewed_at IS NULL
            )
            OR
            (
                status = 'pending_ae_approval'
                AND reviewed_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
                AND ae_reviewed_by_user_id IS NULL
                AND ae_reviewed_at IS NULL
            )
            OR
            (
                status IN ('approved', 'rejected')
                AND reviewed_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
                AND (
                    (ae_reviewed_by_user_id IS NULL AND ae_reviewed_at IS NULL)
                    OR
                    (ae_reviewed_by_user_id IS NOT NULL AND ae_reviewed_at IS NOT NULL)
                )
                AND (status = 'rejected' OR ae_reviewed_by_user_id IS NOT NULL)
            )
            """,
            name="ck_tubewell_status_review_state",
        ),

        Index(
            "ux_tubewell_status_one_pending_per_tubewell",
            "tubewell_id",
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
    # SECTION 6: REQUESTING FIELD USER
    # ========================================================

    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ========================================================
    # SECTION 7: REQUESTED OPERATIONAL STATUS
    # active / inactive
    # ========================================================

    requested_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # ========================================================
    # SECTION 8: REQUEST REASON
    # ========================================================

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # ========================================================
    # SECTION 9: REQUEST WORKFLOW STATUS
    # pending / pending_ae_approval / approved / rejected
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
    # Final AE decision is recorded separately from Supervisor review.
    ae_reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ae_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ae_review_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
