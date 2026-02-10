"""v3 diagnostic pipeline: 4-layer diagnosis, progressive assessment, LLM/RAG, tracking, incentive

Revision ID: 019
Revises: 018
Create Date: 2026-02-10

New tables (18):
  change_causes, user_change_cause_scores, intervention_strategies,
  health_competency_assessments, comb_assessments, self_efficacy_assessments,
  obstacle_assessments, support_assessments, intervention_outcomes,
  stage_transition_logs, point_events, user_point_balances,
  incentive_rewards, user_rewards, assessment_sessions, batch_answers,
  llm_call_logs, rag_query_logs

New columns on users:
  health_competency_level, current_stage, growth_level, nickname, avatar_url
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users 表新增 v3 字段 ──
    op.add_column("users", sa.Column("health_competency_level", sa.String(4), server_default="Lv0"))
    op.add_column("users", sa.Column("current_stage", sa.String(4), server_default="S0"))
    op.add_column("users", sa.Column("growth_level", sa.String(4), server_default="G0"))
    op.add_column("users", sa.Column("nickname", sa.String(64), server_default=""))
    op.add_column("users", sa.Column("avatar_url", sa.String(256), server_default=""))

    # ── change_causes (24 改变动因字典) ──
    op.create_table(
        "change_causes",
        sa.Column("id", sa.String(4), primary_key=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("name_zh", sa.String(50), nullable=False),
        sa.Column("name_en", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("assessment_question", sa.Text, nullable=False),
        sa.Column("weight", sa.Float, server_default="1.0"),
    )

    # ── user_change_cause_scores ──
    op.create_table(
        "user_change_cause_scores",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assessment_id", sa.Integer, nullable=False),
        sa.Column("cause_id", sa.String(4), sa.ForeignKey("change_causes.id"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_user_cause_ua", "user_change_cause_scores", ["user_id", "assessment_id"])

    # ── intervention_strategies ──
    op.create_table(
        "intervention_strategies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("stage_code", sa.String(4), nullable=False, index=True),
        sa.Column("readiness_level", sa.String(4), index=True),
        sa.Column("stage_name", sa.String(20), nullable=False),
        sa.Column("cause_code", sa.String(4), nullable=False, index=True),
        sa.Column("cause_category", sa.String(30), nullable=False),
        sa.Column("cause_name", sa.String(30), nullable=False),
        sa.Column("strategy_type", sa.String(30), nullable=False),
        sa.Column("coach_script", sa.Text, nullable=False),
    )
    op.create_index("ix_strat_rc", "intervention_strategies", ["readiness_level", "cause_code"])

    # ── health_competency_assessments ──
    op.create_table(
        "health_competency_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("level_scores", sa.JSON, nullable=False),
        sa.Column("current_level", sa.String(4), nullable=False),
        sa.Column("recommended_content_stage", sa.String(20)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── comb_assessments ──
    op.create_table(
        "comb_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("dimension_scores", sa.JSON, nullable=False),
        sa.Column("bottleneck", sa.String(20)),
        sa.Column("total_score", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── self_efficacy_assessments ──
    op.create_table(
        "self_efficacy_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("avg_score", sa.Float, nullable=False),
        sa.Column("level", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── obstacle_assessments ──
    op.create_table(
        "obstacle_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("category_scores", sa.JSON, nullable=False),
        sa.Column("top_obstacles", sa.JSON, nullable=False),
        sa.Column("rx_adjustments", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── support_assessments ──
    op.create_table(
        "support_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("layer_scores", sa.JSON, nullable=False),
        sa.Column("total_score", sa.Float, nullable=False),
        sa.Column("support_level", sa.String(10), nullable=False),
        sa.Column("weakest_layer", sa.String(20)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── intervention_outcomes (效果追踪 PDCA) ──
    op.create_table(
        "intervention_outcomes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("date", sa.DateTime, nullable=False),
        sa.Column("tasks_assigned", sa.Integer),
        sa.Column("tasks_completed", sa.Integer),
        sa.Column("tasks_skipped", sa.Integer, server_default="0"),
        sa.Column("completion_rate", sa.Float),
        sa.Column("streak_days", sa.Integer, server_default="0"),
        sa.Column("user_mood", sa.Integer, nullable=True),
        sa.Column("user_difficulty", sa.Integer, nullable=True),
        sa.Column("user_notes", sa.Text, server_default=""),
        sa.Column("cultivation_stage", sa.String(32)),
        sa.Column("spi_before", sa.Float, nullable=True),
        sa.Column("spi_after", sa.Float, nullable=True),
        sa.Column("spi_delta", sa.Float, nullable=True),
        sa.Column("effectiveness_score", sa.Float, nullable=True),
        sa.Column("pdca_action", sa.String(16), nullable=True),
        sa.Column("adjustment_detail", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── stage_transition_logs ──
    op.create_table(
        "stage_transition_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("from_stage", sa.String(8)),
        sa.Column("to_stage", sa.String(8)),
        sa.Column("direction", sa.String(16)),
        sa.Column("trigger", sa.String(32)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── v3 point_events (积分事件) ──
    op.create_table(
        "v3_point_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("points", sa.Integer, nullable=False),
        sa.Column("description", sa.String(128)),
        sa.Column("ref_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── v3 user_point_balances ──
    op.create_table(
        "v3_user_point_balances",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("total_points", sa.Integer, server_default="0"),
        sa.Column("available_points", sa.Integer, server_default="0"),
        sa.Column("growth_level", sa.String(4), server_default="G0"),
        sa.Column("current_streak", sa.Integer, server_default="0"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── incentive_rewards ──
    op.create_table(
        "incentive_rewards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("cost_points", sa.Integer, nullable=False),
        sa.Column("reward_type", sa.String(32)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
    )

    # ── user_rewards ──
    op.create_table(
        "user_rewards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reward_id", sa.Integer, sa.ForeignKey("incentive_rewards.id")),
        sa.Column("points_spent", sa.Integer),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── assessment_sessions (渐进式评估会话) ──
    op.create_table(
        "assessment_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("status", sa.String(16), server_default="in_progress"),
        sa.Column("completed_batches", sa.JSON, server_default=sa.text("'[]'")),
        sa.Column("total_duration_seconds", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── batch_answers ──
    op.create_table(
        "batch_answers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("assessment_sessions.id")),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("batch_id", sa.String(32), nullable=False),
        sa.Column("answers", sa.JSON),
        sa.Column("scores", sa.JSON, nullable=True),
        sa.Column("duration_seconds", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── llm_call_logs ──
    op.create_table(
        "llm_call_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("session_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("intent", sa.String(32)),
        sa.Column("complexity", sa.String(16)),
        sa.Column("model_requested", sa.String(64)),
        sa.Column("model_actual", sa.String(64)),
        sa.Column("provider", sa.String(32)),
        sa.Column("fell_back", sa.Boolean, server_default=sa.text("false")),
        sa.Column("input_tokens", sa.Integer, server_default="0"),
        sa.Column("output_tokens", sa.Integer, server_default="0"),
        sa.Column("cost_yuan", sa.Float, server_default="0"),
        sa.Column("latency_ms", sa.Integer, server_default="0"),
        sa.Column("finish_reason", sa.String(32)),
        sa.Column("user_message_preview", sa.Text),
        sa.Column("assistant_message_preview", sa.Text),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index("ix_llm_logs_user_date", "llm_call_logs", ["user_id", "created_at"])

    # ── rag_query_logs ──
    op.create_table(
        "rag_query_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("query_text", sa.Text),
        sa.Column("query_type", sa.String(32)),
        sa.Column("doc_type_filter", sa.String(32)),
        sa.Column("top_k", sa.Integer, server_default="5"),
        sa.Column("results_count", sa.Integer, server_default="0"),
        sa.Column("top_score", sa.Float, server_default="0"),
        sa.Column("avg_score", sa.Float, server_default="0"),
        sa.Column("sources_json", sa.Text),
        sa.Column("total_latency_ms", sa.Integer, server_default="0"),
        sa.Column("llm_call_log_id", sa.Integer, nullable=True),
    )


def downgrade() -> None:
    tables = [
        "rag_query_logs", "llm_call_logs",
        "batch_answers", "assessment_sessions",
        "user_rewards", "incentive_rewards", "v3_user_point_balances", "v3_point_events",
        "stage_transition_logs", "intervention_outcomes",
        "support_assessments", "obstacle_assessments",
        "self_efficacy_assessments", "comb_assessments",
        "health_competency_assessments", "intervention_strategies",
        "user_change_cause_scores", "change_causes",
    ]
    for t in tables:
        op.drop_table(t)

    op.drop_column("users", "avatar_url")
    op.drop_column("users", "nickname")
    op.drop_column("users", "growth_level")
    op.drop_column("users", "current_stage")
    op.drop_column("users", "health_competency_level")
