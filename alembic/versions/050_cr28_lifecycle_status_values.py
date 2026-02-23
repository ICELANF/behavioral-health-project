"""
Alembic Migration 050 — CR-28 生命周期状态值完善

companion_relations.status 列 (String(20)) 已有值: active/graduated/dropped
新增有效值: pending/cooling/dormant/dissolved

添加 CHECK 约束确保只使用有效状态值。

Revision ID: 050
Revises: 049
"""
from alembic import op
import sqlalchemy as sa


revision = "050"
down_revision = "049"
branch_labels = None
depends_on = None

VALID_STATUSES = "('pending','active','cooling','dormant','dissolved','graduated','dropped')"


def upgrade():
    # Add CHECK constraint for valid status values
    op.execute(
        f"ALTER TABLE companion_relations "
        f"ADD CONSTRAINT ck_cr_status_valid "
        f"CHECK (status IN {VALID_STATUSES})"
    )

    # Set any NULL status to 'active' (defensive)
    op.execute(
        "UPDATE companion_relations SET status = 'active' WHERE status IS NULL"
    )


def downgrade():
    op.execute(
        "ALTER TABLE companion_relations DROP CONSTRAINT IF EXISTS ck_cr_status_valid"
    )
