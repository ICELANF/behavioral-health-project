"""P5B: analytics_daily table for pre-computed metrics.

Revision ID: 047
Revises: 046
"""
from alembic import op
import sqlalchemy as sa

revision = "047"
down_revision = "046"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analytics_daily",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False, unique=True),
        sa.Column("dau", sa.Integer(), server_default="0"),
        sa.Column("new_users", sa.Integer(), server_default="0"),
        sa.Column("active_growers", sa.Integer(), server_default="0"),
        sa.Column("conversion_rate", sa.Float(), server_default="0.0"),
        sa.Column("retention_7d", sa.Float(), server_default="0.0"),
        sa.Column("avg_tasks_completed", sa.Float(), server_default="0.0"),
        sa.Column("avg_session_minutes", sa.Float(), server_default="0.0"),
        sa.Column("ai_response_avg_ms", sa.Float(), server_default="0.0"),
        sa.Column("total_events", sa.Integer(), server_default="0"),
        sa.Column("total_chat_messages", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade():
    op.drop_table("analytics_daily")
