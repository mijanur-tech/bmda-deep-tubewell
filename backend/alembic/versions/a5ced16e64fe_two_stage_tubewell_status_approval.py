"""Two-stage tubewell status approval.

Revision ID: a5ced16e64fe
Revises: 24b3fb715c03

Apply only with coordinated application rollout and a verified database backup.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a5ced16e64fe"
down_revision: Union[str, Sequence[str], None] = "24b3fb715c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Preserve the existing supervisor review fields and historical rows.
    op.add_column("tubewell_status_requests", sa.Column("ae_reviewed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("tubewell_status_requests", sa.Column("ae_reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("tubewell_status_requests", sa.Column("ae_review_comment", sa.String(length=500), nullable=True))
    op.create_foreign_key(
        "fk_tubewell_status_requests_ae_reviewer",
        "tubewell_status_requests", "users",
        ["ae_reviewed_by_user_id"], ["id"],
    )

    op.drop_constraint("ck_tubewell_status_request_status", "tubewell_status_requests", type_="check")
    op.create_check_constraint(
        "ck_tubewell_status_request_status", "tubewell_status_requests",
        "status IN ('pending', 'pending_ae_approval', 'approved', 'rejected')",
    )
    op.drop_constraint("ck_tubewell_status_review_state", "tubewell_status_requests", type_="check")
    op.create_check_constraint(
        "ck_tubewell_status_review_state", "tubewell_status_requests",
        """(
          status = 'pending'
          AND reviewed_by_user_id IS NULL AND reviewed_at IS NULL
          AND ae_reviewed_by_user_id IS NULL AND ae_reviewed_at IS NULL
        ) OR (
          status = 'pending_ae_approval'
          AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL
          AND ae_reviewed_by_user_id IS NULL AND ae_reviewed_at IS NULL
        ) OR (
          status IN ('approved', 'rejected')
          AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL
          AND (
            (ae_reviewed_by_user_id IS NULL AND ae_reviewed_at IS NULL)
            OR (ae_reviewed_by_user_id IS NOT NULL AND ae_reviewed_at IS NOT NULL)
          )
          AND (status = 'rejected' OR ae_reviewed_by_user_id IS NOT NULL)
        )""",
    )
    op.drop_index("ux_tubewell_status_one_pending_per_tubewell", table_name="tubewell_status_requests")
    op.create_index(
        "ux_tubewell_status_one_pending_per_tubewell", "tubewell_status_requests",
        ["tubewell_id"], unique=True,
        postgresql_where=sa.text("status IN ('pending', 'pending_ae_approval')"),
    )


def downgrade() -> None:
    # Refuse to discard active AE-stage requests or populated AE review audit data.
    connection = op.get_bind()
    unsafe_count = connection.execute(sa.text("""
        SELECT COUNT(*) FROM tubewell_status_requests
        WHERE status = 'pending_ae_approval'
           OR ae_reviewed_by_user_id IS NOT NULL
           OR ae_reviewed_at IS NOT NULL
           OR ae_review_comment IS NOT NULL
    """)).scalar_one()
    if unsafe_count:
        raise RuntimeError("Downgrade blocked: AE-stage requests or AE review history exist")

    op.drop_index("ux_tubewell_status_one_pending_per_tubewell", table_name="tubewell_status_requests")
    op.create_index(
        "ux_tubewell_status_one_pending_per_tubewell", "tubewell_status_requests",
        ["tubewell_id"], unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_constraint("ck_tubewell_status_review_state", "tubewell_status_requests", type_="check")
    op.create_check_constraint(
        "ck_tubewell_status_review_state", "tubewell_status_requests",
        """(status = 'pending' AND reviewed_by_user_id IS NULL AND reviewed_at IS NULL)
        OR (status IN ('approved','rejected') AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL)""",
    )
    op.drop_constraint("ck_tubewell_status_request_status", "tubewell_status_requests", type_="check")
    op.create_check_constraint(
        "ck_tubewell_status_request_status", "tubewell_status_requests",
        "status IN ('pending','approved','rejected')",
    )
    op.drop_constraint("fk_tubewell_status_requests_ae_reviewer", "tubewell_status_requests", type_="foreignkey")
    op.drop_column("tubewell_status_requests", "ae_review_comment")
    op.drop_column("tubewell_status_requests", "ae_reviewed_at")
    op.drop_column("tubewell_status_requests", "ae_reviewed_by_user_id")
