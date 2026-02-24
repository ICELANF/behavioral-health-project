# -*- coding: utf-8 -*-
"""
Alembic Migration 052 — 审计治理: 督导资质 + 角色变更日志 + 租户扩展 + 循证等级

新表:
  - supervisor_credentials (I-07: 督导资质生命周期)
  - role_change_logs (I-01: 双轨角色升级审计)

ALTER:
  - expert_tenants: +7列 (I-01 credential_type/role_confirmed, I-02 activated_at/workspace_ready/suspension_count)
  - coach_schema.agent_templates: +evidence_tier (I-09 循证等级)

Revision ID: 052
Revises: 050
"""
from alembic import op
import sqlalchemy as sa

revision = "052"
down_revision = "050"
branch_labels = None
depends_on = None


def upgrade():
    # ── 新表 1: supervisor_credentials (I-07) ──
    op.create_table(
        "supervisor_credentials",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credential_type", sa.String(30), nullable=False, comment="physician_license / coach_certification / phd_supervision"),
        sa.Column("credential_number", sa.String(100), nullable=True, comment="证书编号"),
        sa.Column("issuing_authority", sa.String(200), nullable=True, comment="颁发机构"),
        sa.Column("issued_at", sa.DateTime, nullable=True, comment="颁发日期"),
        sa.Column("expires_at", sa.DateTime, nullable=True, comment="到期日期"),
        sa.Column("status", sa.String(20), server_default="active", nullable=False, comment="active/expired/revoked"),
        sa.Column("granted_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True, comment="授予操作者"),
        sa.Column("granted_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("last_review_at", sa.DateTime, nullable=True, comment="上次年审日期"),
        sa.Column("next_review_at", sa.DateTime, nullable=True, comment="下次年审截止"),
        sa.Column("revoked_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Column("revoke_reason", sa.String(500), nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
    )
    op.create_index("idx_supercred_user_status", "supervisor_credentials", ["user_id", "status"])
    op.create_index("idx_supercred_next_review", "supervisor_credentials", ["next_review_at", "status"])

    # ── 新表 2: role_change_logs (I-01) ──
    op.create_table(
        "role_change_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_role", sa.String(30), nullable=False),
        sa.Column("new_role", sa.String(30), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False, comment="application_approved / credential_granted / credential_revoked / manual"),
        sa.Column("changed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("detail", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_rcl_user_created", "role_change_logs", ["user_id", "created_at"])

    # ── ALTER expert_tenants: +7列 (I-01/I-02) ──
    op.add_column("expert_tenants", sa.Column("credential_type", sa.String(30), nullable=True, comment="physician_license / coach_certification / phd_supervision"))
    op.add_column("expert_tenants", sa.Column("role_confirmed", sa.Boolean, server_default=sa.text("false"), nullable=False))
    op.add_column("expert_tenants", sa.Column("role_confirmed_by", sa.Integer, nullable=True))
    op.add_column("expert_tenants", sa.Column("role_confirmed_at", sa.DateTime, nullable=True))
    op.add_column("expert_tenants", sa.Column("activated_at", sa.DateTime, nullable=True))
    op.add_column("expert_tenants", sa.Column("suspension_count", sa.Integer, server_default="0", nullable=False))
    op.add_column("expert_tenants", sa.Column("workspace_ready", sa.Boolean, server_default=sa.text("false"), nullable=False))

    # ── ALTER coach_schema.agent_templates: +evidence_tier (I-09) ──
    op.add_column(
        "agent_templates",
        sa.Column("evidence_tier", sa.String(5), server_default="T3", nullable=False, comment="T1/T2/T3/T4 循证等级"),
        schema="coach_schema",
    )


def downgrade():
    op.drop_column("agent_templates", "evidence_tier", schema="coach_schema")

    op.drop_column("expert_tenants", "workspace_ready")
    op.drop_column("expert_tenants", "suspension_count")
    op.drop_column("expert_tenants", "activated_at")
    op.drop_column("expert_tenants", "role_confirmed_at")
    op.drop_column("expert_tenants", "role_confirmed_by")
    op.drop_column("expert_tenants", "role_confirmed")
    op.drop_column("expert_tenants", "credential_type")

    op.drop_index("idx_rcl_user_created", table_name="role_change_logs")
    op.drop_table("role_change_logs")

    op.drop_index("idx_supercred_next_review", table_name="supervisor_credentials")
    op.drop_index("idx_supercred_user_status", table_name="supervisor_credentials")
    op.drop_table("supervisor_credentials")
