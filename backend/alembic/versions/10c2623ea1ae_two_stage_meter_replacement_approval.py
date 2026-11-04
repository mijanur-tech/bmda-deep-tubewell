
"""Two-stage meter replacement approval.

Revision ID: 10c2623ea1ae
Revises: a5ced16e64fe

Apply only after coordinated backend rollout and verified backup.
"""

# ============================================================
# SECTION 1: IMPORTS AND REVISION
# ============================================================

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "10c2623ea1ae"
down_revision: Union[str, Sequence[str], None] = "a5ced16e64fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# SECTION 2: UPGRADE
# ============================================================

def upgrade() -> None:

    # --------------------------------------------------------
    # 2.1 Preserve SAE review; add separate AE review fields
    # --------------------------------------------------------

    op.add_column(
        "meter_replacement_requests",
        sa.Column(
            "ae_reviewed_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "meter_replacement_requests",
        sa.Column(
            "ae_reviewed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "meter_replacement_requests",
        sa.Column(
            "ae_review_comment",
            sa.String(length=500),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_meter_replacement_requests_ae_reviewer",
        "meter_replacement_requests",
        "users",
        ["ae_reviewed_by_user_id"],
        ["id"],
    )

    # --------------------------------------------------------
    # 2.2 Allow new intermediate approval status
    # --------------------------------------------------------

    op.drop_constraint(
        "ck_meter_replacement_status",
        "meter_replacement_requests",
        type_="check",
    )

    op.create_check_constraint(
        "ck_meter_replacement_status",
        "meter_replacement_requests",
        """
        status IN (
            'pending',
            'pending_ae_approval',
            'approved',
            'rejected'
        )
        """,
    )

    # --------------------------------------------------------
    # 2.3 Enforce SAE and AE review state
    # --------------------------------------------------------

    op.drop_constraint(
        "ck_meter_replacement_review_state",
        "meter_replacement_requests",
        type_="check",
    )

    op.create_check_constraint(
        "ck_meter_replacement_review_state",
        "meter_replacement_requests",
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
    )

    # --------------------------------------------------------
    # 2.4 Prevent duplicate requests at both pending stages
    # --------------------------------------------------------

    op.drop_index(
        "ux_meter_replacement_one_pending_per_tubewell",
        table_name="meter_replacement_requests",
    )

    op.create_index(
        "ux_meter_replacement_one_pending_per_tubewell",
        "meter_replacement_requests",
        ["tubewell_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending', 'pending_ae_approval')"
        ),
    )


# ============================================================
# SECTION 3: SAFE DOWNGRADE
# ============================================================

def downgrade() -> None:

    connection = op.get_bind()

    unsafe_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM meter_replacement_requests
            WHERE status = 'pending_ae_approval'
               OR ae_reviewed_by_user_id IS NOT NULL
               OR ae_reviewed_at IS NOT NULL
               OR ae_review_comment IS NOT NULL
            """
        )
    ).scalar_one()

    if unsafe_count:
        raise RuntimeError(
            "Downgrade blocked: AE-stage requests "
            "or AE review history exist."
        )

    # --------------------------------------------------------
    # 3.1 Restore original pending index
    # --------------------------------------------------------

    op.drop_index(
        "ux_meter_replacement_one_pending_per_tubewell",
        table_name="meter_replacement_requests",
    )

    op.create_index(
        "ux_meter_replacement_one_pending_per_tubewell",
        "meter_replacement_requests",
        ["tubewell_id"],
        unique=True,
        postgresql_where=sa.text(
            "status = 'pending'"
        ),
    )

    # --------------------------------------------------------
    # 3.2 Restore original review constraints
    # --------------------------------------------------------

    op.drop_constraint(
        "ck_meter_replacement_review_state",
        "meter_replacement_requests",
        type_="check",
    )

    op.create_check_constraint(
        "ck_meter_replacement_review_state",
        "meter_replacement_requests",
        """
        (
            status = 'pending'
            AND reviewed_by_user_id IS NULL
            AND reviewed_at IS NULL
            AND new_meter_id IS NULL
        )
        OR
        (
            status = 'approved'
            AND reviewed_by_user_id IS NOT NULL
            AND reviewed_at IS NOT NULL
            AND new_meter_id IS NOT NULL
        )
        OR
        (
            status = 'rejected'
            AND reviewed_by_user_id IS NOT NULL
            AND reviewed_at IS NOT NULL
            AND new_meter_id IS NULL
        )
        """,
    )

    op.drop_constraint(
        "ck_meter_replacement_status",
        "meter_replacement_requests",
        type_="check",
    )

    op.create_check_constraint(
        "ck_meter_replacement_status",
        "meter_replacement_requests",
        "status IN ('pending', 'approved', 'rejected')",
    )

    # --------------------------------------------------------
    # 3.3 Remove AE-only fields
    # --------------------------------------------------------

    op.drop_constraint(
        "fk_meter_replacement_requests_ae_reviewer",
        "meter_replacement_requests",
        type_="foreignkey",
    )

    op.drop_column(
        "meter_replacement_requests",
        "ae_review_comment",
    )

    op.drop_column(
        "meter_replacement_requests",
        "ae_reviewed_at",
    )

    op.drop_column(
        "meter_replacement_requests",
        "ae_reviewed_by_user_id",
    )
