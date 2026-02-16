"""
Alembic Migration 041 — 中医骨科康复扩展表 (V4.3)

新增3张表:
  1. pain_assessments (public) — 疼痛评估记录
  2. rehab_plans (coach_schema) — 康复方案
  3. tcm_syndrome_records (coach_schema) — 中医辨证记录

Revision ID: 041
Revises: 040
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ────────────────────────────────────────
    # 1. pain_assessments (public schema)
    #    用户疼痛评估记录, 用户层可读写
    # ────────────────────────────────────────
    op.create_table(
        "pain_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"),
                  nullable=False, index=True),
        sa.Column("engine_name", sa.String(50), nullable=False,
                  comment="评估引擎: PainScaleEngine/PainAssessEngine"),
        sa.Column("nrs_score", sa.SmallInteger,
                  comment="NRS疼痛评分 0-10"),
        sa.Column("pain_location", sa.String(100),
                  comment="疼痛部位"),
        sa.Column("pain_type", sa.String(50),
                  comment="疼痛类型: 伤害性/神经病理性/混合性"),
        sa.Column("duration_days", sa.Integer, default=0,
                  comment="持续天数"),
        sa.Column("is_chronic", sa.Boolean, default=False,
                  comment="是否慢性(≥90天)"),
        sa.Column("classification", sa.String(100),
                  comment="综合分类结果"),
        sa.Column("scores", JSONB, default={},
                  comment="评分详情JSON"),
        sa.Column("functional_impact", JSONB, default={},
                  comment="BPI功能影响JSON"),
        sa.Column("recommendations", JSONB, default=[],
                  comment="建议列表JSON"),
        sa.Column("raw_answers", JSONB, default={},
                  comment="原始答题JSON"),
        sa.Column("assessed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema=None,  # public schema
    )

    # 查询索引: 按用户+时间
    op.create_index(
        "ix_pain_assessments_user_time",
        "pain_assessments",
        ["user_id", "assessed_at"],
    )

    # ────────────────────────────────────────
    # 2. rehab_plans (coach_schema)
    #    康复方案, 教练层管理
    # ────────────────────────────────────────
    op.execute("SET search_path TO coach_schema, public")

    op.create_table(
        "rehab_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Integer, nullable=False, index=True,
                  comment="关联public.users.id"),
        sa.Column("coach_id", sa.Integer, nullable=True,
                  comment="负责教练ID"),
        sa.Column("diagnosis", sa.String(200),
                  comment="诊断/问题描述"),
        sa.Column("current_stage", sa.String(50),
                  comment="当前阶段: 急性期/亚急性期/恢复期/强化期/维持期"),
        sa.Column("onset_date", sa.Date, nullable=True,
                  comment="发病/术后日期"),
        sa.Column("is_postop", sa.Boolean, default=False),
        sa.Column("total_weeks", sa.SmallInteger, default=12,
                  comment="计划总周数"),
        sa.Column("current_week", sa.SmallInteger, default=1,
                  comment="当前周"),
        sa.Column("progress_pct", sa.Float, default=0,
                  comment="康复进度百分比"),
        sa.Column("plan_content", JSONB, default={},
                  comment="完整方案JSON(weekly_plans/milestones/etc)"),
        sa.Column("latest_assessment", JSONB, default={},
                  comment="最新评估结果JSON(NRS/ROM/Strength)"),
        sa.Column("stage_history", JSONB, default=[],
                  comment="阶段变更历史JSON"),
        sa.Column("status", sa.String(20), default="active",
                  comment="active/paused/completed/cancelled"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"),
                  onupdate=sa.text("now()")),
        schema="coach_schema",
    )

    # ────────────────────────────────────────
    # 3. tcm_syndrome_records (coach_schema)
    #    中医辨证记录, 教练层管理
    # ────────────────────────────────────────
    op.create_table(
        "tcm_syndrome_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("coach_id", sa.Integer, nullable=True),
        sa.Column("primary_syndrome", sa.String(50),
                  comment="主证型"),
        sa.Column("secondary_syndrome", sa.String(50), nullable=True,
                  comment="兼证型"),
        sa.Column("symptoms", JSONB, default=[],
                  comment="症状列表JSON"),
        sa.Column("tongue_pulse", sa.String(200), nullable=True,
                  comment="舌脉描述"),
        sa.Column("pain_location", sa.String(100)),
        sa.Column("acupoint_prescription", JSONB, default={},
                  comment="穴位处方JSON"),
        sa.Column("external_prescription", JSONB, default=[],
                  comment="外用方JSON"),
        sa.Column("tuina_protocol", JSONB, default={},
                  comment="推拿方案JSON"),
        sa.Column("contraindications", JSONB, default=[],
                  comment="禁忌列表JSON"),
        sa.Column("safety_notes", JSONB, default=[],
                  comment="安全注意事项JSON"),
        sa.Column("review_status", sa.String(20), default="pending",
                  comment="pending/approved/rejected"),
        sa.Column("reviewer_id", sa.Integer, nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema="coach_schema",
    )

    # 重置search_path
    op.execute("SET search_path TO public")


def downgrade() -> None:
    op.execute("SET search_path TO coach_schema, public")
    op.drop_table("tcm_syndrome_records", schema="coach_schema")
    op.drop_table("rehab_plans", schema="coach_schema")
    op.execute("SET search_path TO public")

    op.drop_index("ix_pain_assessments_user_time", table_name="pain_assessments")
    op.drop_table("pain_assessments")
