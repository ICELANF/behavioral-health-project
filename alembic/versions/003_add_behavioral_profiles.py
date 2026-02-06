"""Add behavioral_profiles table

Revision ID: 003
Revises: 002
Create Date: 2026-02-06

Adds the unified BehavioralProfile table that serves as the system's
single source of truth for each user's behavioral change stage,
personality type, psychological level, and domain intervention needs.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create behavioral_profiles table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "behavioral_profiles" not in existing_tables:
        op.create_table(
            "behavioral_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, nullable=False),

            # 阶段运行态
            sa.Column("current_stage", sa.String(5), nullable=False, server_default="S0"),
            sa.Column("stage_confidence", sa.Float(), server_default="0.0"),
            sa.Column("stage_stability", sa.String(15), server_default="unstable"),
            sa.Column("stage_updated_at", sa.DateTime(), nullable=True),

            # BAPS 向量
            sa.Column("big5_scores", sa.JSON(), nullable=True),
            sa.Column("bpt6_type", sa.String(30), nullable=True),
            sa.Column("bpt6_scores", sa.JSON(), nullable=True),
            sa.Column("capacity_total", sa.Integer(), nullable=True),
            sa.Column("capacity_weak", sa.JSON(), nullable=True),
            sa.Column("capacity_strong", sa.JSON(), nullable=True),
            sa.Column("spi_score", sa.Float(), nullable=True),
            sa.Column("spi_level", sa.String(10), nullable=True),
            sa.Column("ttm7_stage_scores", sa.JSON(), nullable=True),
            sa.Column("ttm7_sub_scores", sa.JSON(), nullable=True),

            # 领域需求
            sa.Column("primary_domains", sa.JSON(), nullable=True),
            sa.Column("domain_details", sa.JSON(), nullable=True),

            # 干预配置
            sa.Column("interaction_mode", sa.String(15), nullable=True),
            sa.Column("psychological_level", sa.String(5), nullable=True),
            sa.Column("risk_flags", sa.JSON(), nullable=True),

            # 去诊断化展示
            sa.Column("friendly_stage_name", sa.String(50), nullable=True),
            sa.Column("friendly_stage_desc", sa.Text(), nullable=True),

            # 溯源
            sa.Column("last_assessment_id", sa.String(50), nullable=True),

            # 时间戳
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

        op.create_index("idx_bp_user", "behavioral_profiles", ["user_id"])
        op.create_index("idx_bp_stage", "behavioral_profiles", ["current_stage"])
        op.create_index("idx_bp_updated", "behavioral_profiles", ["updated_at"])


def downgrade() -> None:
    """Drop behavioral_profiles table."""
    op.drop_index("idx_bp_updated", table_name="behavioral_profiles")
    op.drop_index("idx_bp_stage", table_name="behavioral_profiles")
    op.drop_index("idx_bp_user", table_name="behavioral_profiles")
    op.drop_table("behavioral_profiles")
