"""Add Energy and Prepaid meter types.

Revision ID: 579a2d10f946
Revises: 10c2623ea1ae
Create Date: 2026-10-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# Alembic Revision Information
# ============================================================

revision: str = "579a2d10f946"

down_revision: Union[str, Sequence[str], None] = "10c2623ea1ae"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# Upgrade
# ============================================================

def upgrade() -> None:
    """Introduce separate Energy and Prepaid meter management."""

    # --------------------------------------------------------
    # 1. Add meter_type to meters
    # --------------------------------------------------------

    op.add_column(
        "meters",
        sa.Column(
            "meter_type",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # --------------------------------------------------------
    # 2. Add meter_type to replacement requests
    # --------------------------------------------------------

    op.add_column(
        "meter_replacement_requests",
        sa.Column(
            "meter_type",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # --------------------------------------------------------
    # 3. Restrict valid meter types
    # --------------------------------------------------------

    op.create_check_constraint(
        "ck_meters_meter_type",
        "meters",
        "meter_type IN ('energy', 'prepaid')",
    )

    op.create_check_constraint(
        "ck_meter_replacement_meter_type",
        "meter_replacement_requests",
        "meter_type IN ('energy', 'prepaid')",
    )

    # --------------------------------------------------------
    # 4. Require type for replacement requests
    # --------------------------------------------------------

    op.alter_column(
        "meter_replacement_requests",
        "meter_type",
        existing_type=sa.String(length=20),
        nullable=False,
    )

    # --------------------------------------------------------
    # 5. Replace old pending request uniqueness
    # --------------------------------------------------------

    op.drop_index(
        "ux_meter_replacement_one_pending_per_tubewell",
        table_name="meter_replacement_requests",
    )

    # --------------------------------------------------------
    # 6. Unique pending request per tubewell + meter type
    # --------------------------------------------------------

    op.create_index(
        "ux_meter_replacement_pending_per_tubewell_type",
        "meter_replacement_requests",
        ["tubewell_id", "meter_type"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending', 'pending_ae_approval')"
        ),
    )


# ============================================================
# Downgrade
# ============================================================

def downgrade() -> None:
    """Restore the previous single-type replacement structure."""

    # --------------------------------------------------------
    # 1. Restore previous pending request uniqueness
    # --------------------------------------------------------

    op.drop_index(
        "ux_meter_replacement_pending_per_tubewell_type",
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

    # --------------------------------------------------------
    # 2. Remove meter type constraints
    # --------------------------------------------------------

    op.drop_constraint(
        "ck_meter_replacement_meter_type",
        "meter_replacement_requests",
        type_="check",
    )

    op.drop_constraint(
        "ck_meters_meter_type",
        "meters",
        type_="check",
    )

    # --------------------------------------------------------
    # 3. Remove meter type columns
    # --------------------------------------------------------

    op.drop_column(
        "meter_replacement_requests",
        "meter_type",
    )

    op.drop_column(
        "meters",
        "meter_type",
    )
