"""migration_031_behavior_rx_foundation

行为处方基座 — 3 张新表
  1. rx_prescriptions       — 行为处方记录
  2. rx_strategy_templates  — 行为策略模板库
  3. agent_handoff_log      — Agent 交接日志

Revision ID: 031_behavior_rx
Revises: 029 (skill_graph)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "031_behavior_rx"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 表 1: rx_prescriptions — 行为处方记录
    # ------------------------------------------------------------------
    op.create_table(
        "rx_prescriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        # 关联
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(32), nullable=False),
        # 三维输入
        sa.Column("ttm_stage", sa.Integer, nullable=False),
        sa.Column("bigfive_profile", JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("capacity_score", sa.Float, nullable=False, server_default=sa.text("0.5")),
        # 处方输出
        sa.Column("goal_behavior", sa.Text, nullable=False),
        sa.Column("strategy_type", sa.String(48), nullable=False),
        sa.Column("secondary_strategies", JSONB, nullable=True,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("intensity", sa.String(16), nullable=False),
        sa.Column("pace", sa.String(32), nullable=False, server_default=sa.text("'standard'")),
        sa.Column("communication_style", sa.String(24), nullable=False),
        # 微行动 & 执行参数
        sa.Column("micro_actions", JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("reward_triggers", JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("resistance_threshold", sa.Float, nullable=False,
                  server_default=sa.text("0.3")),
        sa.Column("escalation_rules", JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        # 领域包装
        sa.Column("domain_context", JSONB, nullable=True,
                  server_default=sa.text("'{}'::jsonb")),
        # 效果追踪
        sa.Column("effectiveness_score", sa.Float, nullable=True),
        sa.Column("adherence_index", sa.Float, nullable=True),
        sa.Column("outcome_label", sa.String(32), nullable=True),
        # 元数据
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("superseded_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_rx_prescriptions_user_id", "rx_prescriptions", ["user_id"])
    op.create_index("ix_rx_prescriptions_session_id", "rx_prescriptions", ["session_id"])
    op.create_index("ix_rx_prescriptions_agent_type", "rx_prescriptions", ["agent_type"])
    op.create_index("ix_rx_prescriptions_created_at", "rx_prescriptions", ["created_at"])
    op.create_index("ix_rx_prescriptions_user_active",
                    "rx_prescriptions", ["user_id", "agent_type", "is_active"])

    # ------------------------------------------------------------------
    # 表 2: rx_strategy_templates — 行为策略模板库
    # ------------------------------------------------------------------
    op.create_table(
        "rx_strategy_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        # 定位维度
        sa.Column("strategy_type", sa.String(48), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False, server_default=sa.text("'general'")),
        sa.Column("ttm_stage_min", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("ttm_stage_max", sa.Integer, nullable=False, server_default=sa.text("6")),
        # 模板内容
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("name_zh", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("core_mechanism", sa.Text, nullable=False),
        sa.Column("typical_applications", JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        # 默认参数
        sa.Column("default_intensity", sa.String(16), nullable=False,
                  server_default=sa.text("'moderate'")),
        sa.Column("default_pace", sa.String(32), nullable=False,
                  server_default=sa.text("'standard'")),
        sa.Column("default_micro_actions", JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("default_reward_triggers", JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("default_resistance_threshold", sa.Float, nullable=False,
                  server_default=sa.text("0.3")),
        # 人格适配
        sa.Column("personality_modifiers", JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        # 管理
        sa.Column("evidence_tier", sa.String(8), nullable=False,
                  server_default=sa.text("'T2'")),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_rx_strategy_templates_type_domain",
                    "rx_strategy_templates", ["strategy_type", "domain"])
    op.create_index("ix_rx_strategy_templates_enabled",
                    "rx_strategy_templates", ["is_enabled"])

    # ------------------------------------------------------------------
    # 表 3: agent_handoff_log — Agent 交接日志
    # ------------------------------------------------------------------
    op.create_table(
        "agent_handoff_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        # 关联
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), nullable=True),
        # 交接方
        sa.Column("from_agent", sa.String(32), nullable=False),
        sa.Column("to_agent", sa.String(32), nullable=False),
        sa.Column("handoff_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'initiated'")),
        # 交接上下文
        sa.Column("rx_context", JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("rx_prescription_id", UUID(as_uuid=True), nullable=True),
        # 触发条件
        sa.Column("trigger_reason", sa.Text, nullable=False),
        sa.Column("trigger_data", JSONB, nullable=True,
                  server_default=sa.text("'{}'::jsonb")),
        # 结果
        sa.Column("outcome", JSONB, nullable=True,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        # 时间戳
        sa.Column("initiated_at", sa.DateTime, nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_agent_handoff_log_user_id", "agent_handoff_log", ["user_id"])
    op.create_index("ix_agent_handoff_log_from_agent", "agent_handoff_log", ["from_agent"])
    op.create_index("ix_agent_handoff_log_to_agent", "agent_handoff_log", ["to_agent"])
    op.create_index("ix_agent_handoff_log_status", "agent_handoff_log", ["status"])
    op.create_index("ix_agent_handoff_log_initiated_at",
                    "agent_handoff_log", ["initiated_at"])


def downgrade() -> None:
    op.drop_table("agent_handoff_log")
    op.drop_table("rx_strategy_templates")
    op.drop_table("rx_prescriptions")
