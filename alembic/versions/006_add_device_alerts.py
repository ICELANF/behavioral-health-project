"""Add device_alerts table

Revision ID: 006
Revises: 005
Create Date: 2026-02-07

Adds table for:
- device_alerts: 设备预警记录
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create device_alerts table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "device_alerts" not in existing_tables:
        op.create_table(
            "device_alerts",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("coach_id", sa.Integer, nullable=True, index=True),
            sa.Column("alert_type", sa.String(50), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False),
            sa.Column("message", sa.String(500), nullable=False),
            sa.Column("data_value", sa.Float, nullable=False),
            sa.Column("threshold_value", sa.Float, nullable=False),
            sa.Column("data_type", sa.String(30), nullable=False),
            sa.Column("user_read", sa.Boolean, server_default="0", nullable=False),
            sa.Column("coach_read", sa.Boolean, server_default="0", nullable=False),
            sa.Column("resolved", sa.Boolean, server_default="0", nullable=False),
            sa.Column("dedup_key", sa.String(100), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_device_alert_user", "device_alerts", ["user_id", "created_at"])
        op.create_index("idx_device_alert_coach", "device_alerts", ["coach_id", "coach_read"])
        op.create_index("idx_device_alert_dedup", "device_alerts", ["dedup_key"])


def downgrade() -> None:
    """Drop device_alerts table."""
    op.drop_table("device_alerts")
