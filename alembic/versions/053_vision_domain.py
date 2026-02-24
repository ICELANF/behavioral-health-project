# -*- coding: utf-8 -*-
"""
Alembic Migration 053 — VisionGuard 视力行为保护域

新表 (5):
  - vision_exam_records      视力检查记录(简化版)
  - vision_behavior_logs     视力行为日志
  - vision_behavior_goals    视力行为目标
  - vision_guardian_bindings  监护人绑定关系
  - vision_profiles          视力专属扩展档案

Revision ID: 053
Revises: 052
"""
from alembic import op
import sqlalchemy as sa

revision = "053"
down_revision = "052"
branch_labels = None
depends_on = None


def upgrade():
    # ── 表 1: vision_exam_records ──
    op.create_table(
        "vision_exam_records",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exam_date", sa.Date, nullable=False),
        sa.Column("left_eye_sph", sa.Float, nullable=True, comment="左眼球镜(负值=近视)"),
        sa.Column("right_eye_sph", sa.Float, nullable=True, comment="右眼球镜"),
        sa.Column("left_eye_cyl", sa.Float, nullable=True, comment="左眼柱镜(散光)"),
        sa.Column("right_eye_cyl", sa.Float, nullable=True, comment="右眼柱镜"),
        sa.Column("left_eye_axial_len", sa.Float, nullable=True, comment="左眼眼轴长度mm"),
        sa.Column("right_eye_axial_len", sa.Float, nullable=True, comment="右眼眼轴长度mm"),
        sa.Column("left_eye_va", sa.Float, nullable=True, comment="左眼视力(5分制)"),
        sa.Column("right_eye_va", sa.Float, nullable=True, comment="右眼视力(5分制)"),
        sa.Column("exam_type", sa.String(30), server_default="routine", nullable=False),
        sa.Column("examiner_name", sa.String(100), nullable=True),
        sa.Column("institution", sa.String(200), nullable=True),
        sa.Column("risk_level", sa.String(20), server_default="normal", nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("raw_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_vision_exam_user_date", "vision_exam_records", ["user_id", "exam_date"])
    op.create_index("idx_vision_exam_risk", "vision_exam_records", ["risk_level"])

    # ── 表 2: vision_behavior_logs ──
    op.create_table(
        "vision_behavior_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date, nullable=False),
        sa.Column("outdoor_minutes", sa.Integer, server_default="0", nullable=False),
        sa.Column("screen_sessions", sa.Integer, server_default="0", nullable=False),
        sa.Column("screen_total_minutes", sa.Integer, server_default="0", nullable=False),
        sa.Column("eye_exercise_done", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("lutein_intake_mg", sa.Float, server_default="0.0", nullable=False),
        sa.Column("sleep_minutes", sa.Integer, server_default="0", nullable=False),
        sa.Column("behavior_score", sa.Float, nullable=True),
        sa.Column("input_source", sa.String(20), server_default="manual", nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "log_date", name="uq_vision_log_user_date"),
    )
    op.create_index("idx_vision_log_user_date", "vision_behavior_logs", ["user_id", "log_date"])
    op.create_index("idx_vision_log_score", "vision_behavior_logs", ["behavior_score"])

    # ── 表 3: vision_behavior_goals ──
    op.create_table(
        "vision_behavior_goals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("outdoor_target_min", sa.Integer, server_default="120", nullable=False),
        sa.Column("screen_session_limit", sa.Integer, server_default="6", nullable=False),
        sa.Column("screen_daily_limit", sa.Integer, server_default="120", nullable=False),
        sa.Column("lutein_target_mg", sa.Float, server_default="10.0", nullable=False),
        sa.Column("sleep_target_min", sa.Integer, server_default="480", nullable=False),
        sa.Column("ttm_stage", sa.String(4), nullable=True),
        sa.Column("auto_adjust", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
    )

    # ── 表 4: vision_guardian_bindings ──
    op.create_table(
        "vision_guardian_bindings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guardian_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship", sa.String(20), server_default="parent", nullable=False),
        sa.Column("notify_risk_threshold", sa.String(20), server_default="watch", nullable=False),
        sa.Column("can_input_behavior", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("deactivated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("student_user_id", "guardian_user_id", name="uq_vision_guardian_pair"),
    )
    op.create_index("idx_vision_guardian_student", "vision_guardian_bindings", ["student_user_id"])
    op.create_index("idx_vision_guardian_guardian", "vision_guardian_bindings", ["guardian_user_id"])

    # ── 表 5: vision_profiles ──
    op.create_table(
        "vision_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("is_vision_student", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("myopia_onset_age", sa.Integer, nullable=True),
        sa.Column("current_risk_level", sa.String(20), server_default="normal", nullable=False),
        sa.Column("ttm_vision_stage", sa.String(4), server_default="S0", nullable=False),
        sa.Column("last_exam_date", sa.Date, nullable=True),
        sa.Column("expert_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("enrolled_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("idx_vision_profile_user", "vision_profiles", ["user_id"])
    op.create_index("idx_vision_profile_risk", "vision_profiles", ["current_risk_level"])


def downgrade():
    op.drop_table("vision_profiles")
    op.drop_table("vision_guardian_bindings")
    op.drop_table("vision_behavior_goals")
    op.drop_table("vision_behavior_logs")
    op.drop_table("vision_exam_records")
