"""
Alembic Migration 042 — CR-28 同道者追踪字段补全

为 companion_relations 表添加 9 个字段，支持:
  - 互动追踪: last_interaction_at, interaction_count, avg_quality_score
  - 互惠性: initiator_count_a, initiator_count_b, reciprocity_score
  - 生命周期: state_changed_at, dissolved_at, dissolve_reason

Revision ID: 042
Revises: 041
"""
from alembic import op
import sqlalchemy as sa


revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade():
    # 互动追踪
    op.add_column("companion_relations", sa.Column(
        "last_interaction_at", sa.DateTime(), nullable=True,
        comment="最后互动时间",
    ))
    op.add_column("companion_relations", sa.Column(
        "interaction_count", sa.Integer(), nullable=True, server_default="0",
        comment="累计互动次数",
    ))
    op.add_column("companion_relations", sa.Column(
        "avg_quality_score", sa.Float(), nullable=True,
        comment="平均互动质量 0.0~1.0",
    ))

    # 互惠性
    op.add_column("companion_relations", sa.Column(
        "initiator_count_a", sa.Integer(), nullable=True, server_default="0",
        comment="mentor方发起互动次数",
    ))
    op.add_column("companion_relations", sa.Column(
        "initiator_count_b", sa.Integer(), nullable=True, server_default="0",
        comment="mentee方发起互动次数",
    ))
    op.add_column("companion_relations", sa.Column(
        "reciprocity_score", sa.Float(), nullable=True,
        comment="互惠分 0.0~1.0 (1.0=完全均衡)",
    ))

    # 生命周期
    op.add_column("companion_relations", sa.Column(
        "state_changed_at", sa.DateTime(), nullable=True,
        comment="状态变更时间",
    ))
    op.add_column("companion_relations", sa.Column(
        "dissolved_at", sa.DateTime(), nullable=True,
        comment="解除时间",
    ))
    op.add_column("companion_relations", sa.Column(
        "dissolve_reason", sa.String(50), nullable=True,
        comment="解除原因: auto_timeout/manual/graduated",
    ))

    # 索引: 按状态+最后互动时间查询 (生命周期批量更新)
    op.create_index(
        "idx_cr_status_last_interaction",
        "companion_relations",
        ["status", "last_interaction_at"],
    )


def downgrade():
    op.drop_index("idx_cr_status_last_interaction", table_name="companion_relations")
    for col in [
        "dissolve_reason", "dissolved_at", "state_changed_at",
        "reciprocity_score", "initiator_count_b", "initiator_count_a",
        "avg_quality_score", "interaction_count", "last_interaction_at",
    ]:
        op.drop_column("companion_relations", col)
