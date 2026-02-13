"""migration_031_expert_self_registration

专家自助注册入驻 — expert_tenants 追加 3 列
  1. application_status  — 申请状态 (pending_review/approved/rejected)
  2. application_data    — 申请表单原始数据 (JSON)
  3. applied_at          — 申请提交时间

Revision ID: 031
Revises: 030 (behavior_rx_foundation)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 追加 3 列到 expert_tenants
    op.add_column(
        "expert_tenants",
        sa.Column("application_status", sa.String(20), nullable=True,
                  comment="pending_review/approved/rejected/NULL(旧数据)"),
    )
    op.add_column(
        "expert_tenants",
        sa.Column("application_data", sa.JSON, nullable=True,
                  server_default="{}",
                  comment="申请表单原始数据"),
    )
    op.add_column(
        "expert_tenants",
        sa.Column("applied_at", sa.DateTime, nullable=True,
                  comment="申请提交时间"),
    )

    # 索引: 按申请状态查询
    op.create_index(
        "idx_tenant_app_status",
        "expert_tenants",
        ["application_status"],
    )

    # 追加 pending_review 到 TenantStatus 枚举
    # PostgreSQL enum 需要 ALTER TYPE
    op.execute("ALTER TYPE tenantstatus ADD VALUE IF NOT EXISTS 'pending_review'")

    # 修补: expert_tenants.created_at/updated_at 缺少 server_default
    op.execute("ALTER TABLE expert_tenants ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE expert_tenants ALTER COLUMN updated_at SET DEFAULT now()")


def downgrade() -> None:
    op.drop_index("idx_tenant_app_status", table_name="expert_tenants")
    op.drop_column("expert_tenants", "applied_at")
    op.drop_column("expert_tenants", "application_data")
    op.drop_column("expert_tenants", "application_status")
    # Note: cannot remove enum value in PostgreSQL
