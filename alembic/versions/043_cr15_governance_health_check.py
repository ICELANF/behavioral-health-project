"""
Alembic Migration 043 — CR-15 治理健康度检查列补全

为 responsibility_metrics 表添加 4 列:
  - metric_type: 区分检查类型 (如 "governance_health_check")
  - value: 综合评分 0.0~1.0
  - detail: 完整检查报告 (JSONB)
  - checked_at: 检查时间戳

同时放宽 user_id, period_start, period_end 为 nullable
(系统级健康检查不关联具体用户/时段)

Revision ID: 043
Revises: 042
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "043"
down_revision = "042"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "responsibility_metrics",
        sa.Column("metric_type", sa.String(50), nullable=True, index=True),
    )
    op.add_column(
        "responsibility_metrics",
        sa.Column("value", sa.Float, nullable=True),
    )
    op.add_column(
        "responsibility_metrics",
        sa.Column("detail", JSONB, nullable=True),
    )
    op.add_column(
        "responsibility_metrics",
        sa.Column("checked_at", sa.DateTime, nullable=True),
    )
    # user_id 原为 NOT NULL, 健康检查属系统级不关联具体用户
    op.alter_column(
        "responsibility_metrics", "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    # metric_code 原为 NOT NULL, 健康检查使用 metric_type 代替
    op.alter_column(
        "responsibility_metrics", "metric_code",
        existing_type=sa.String(20),
        nullable=True,
    )
    # metric_value 原为 NOT NULL, 健康检查使用 value 代替
    op.alter_column(
        "responsibility_metrics", "metric_value",
        existing_type=sa.Float(),
        nullable=True,
    )
    # period_start/period_end 原为 NOT NULL, 健康检查不需要
    op.alter_column(
        "responsibility_metrics", "period_start",
        existing_type=sa.Date(),
        nullable=True,
    )
    op.alter_column(
        "responsibility_metrics", "period_end",
        existing_type=sa.Date(),
        nullable=True,
    )


def downgrade():
    op.alter_column("responsibility_metrics", "period_end",
                     existing_type=sa.Date(), nullable=False)
    op.alter_column("responsibility_metrics", "period_start",
                     existing_type=sa.Date(), nullable=False)
    op.alter_column("responsibility_metrics", "metric_value",
                     existing_type=sa.Float(), nullable=False)
    op.alter_column("responsibility_metrics", "metric_code",
                     existing_type=sa.String(20), nullable=False)
    op.alter_column("responsibility_metrics", "user_id",
                     existing_type=sa.Integer(), nullable=False)
    for col_name in ["checked_at", "detail", "value", "metric_type"]:
        op.drop_column("responsibility_metrics", col_name)
