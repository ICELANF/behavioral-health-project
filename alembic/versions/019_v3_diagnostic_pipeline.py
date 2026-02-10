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
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("outcome_type", sa.String(20), nullable=False),
        sa.Column("period_start", sa.DateTime, nullable=False),
        sa.Column("period_end", sa.DateTime, nullable=False),
        sa.Column("completion_rate", sa.Float),
        sa.Column("streak_days", sa.Integer, server_default="0"),
        sa.Column("tasks_assigned", sa.Integer, server_default="0"),
        sa.Column("tasks_completed", sa.Integer, server_default="0"),
        sa.Column("tasks_skipped", sa.Integer, server_default="0"),
        sa.Column("spi_before", sa.Float, nullable=True),
        sa.Column("spi_after", sa.Float, nullable=True),
        sa.Column("spi_delta", sa.Float, nullable=True),
        sa.Column("stage_before", sa.String(4)),
        sa.Column("stage_after", sa.String(4)),
        sa.Column("readiness_before", sa.String(4)),
        sa.Column("readiness_after", sa.String(4)),
        sa.Column("cultivation_stage", sa.String(20)),
        sa.Column("user_mood", sa.Integer, nullable=True),
        sa.Column("user_difficulty", sa.Integer, nullable=True),
        sa.Column("user_notes", sa.Text),
        sa.Column("effectiveness_score", sa.Float, nullable=True),
        sa.Column("adjustment_action", sa.String(30)),
        sa.Column("adjustment_detail", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_outcome_user_type", "intervention_outcomes", ["user_id", "outcome_type"])
    op.create_index("ix_outcome_user_period", "intervention_outcomes", ["user_id", "period_start"])

    # ── stage_transition_logs ──
    op.create_table(
        "stage_transition_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("transition_type", sa.String(20), nullable=False),
        sa.Column("from_value", sa.String(10), nullable=False),
        sa.Column("to_value", sa.String(10), nullable=False),
        sa.Column("trigger", sa.String(50)),
        sa.Column("evidence", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_stage_trans_user", "stage_transition_logs", ["user_id", "transition_type"])

    # ── point_events (积分事件流水) ──
    op.create_table(
        "point_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("dimension", sa.String(15), nullable=False),
        sa.Column("points", sa.Integer, nullable=False),
        sa.Column("source_type", sa.String(30)),
        sa.Column("source_id", sa.String(50)),
        sa.Column("description", sa.String(200)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_point_user_dim", "point_events", ["user_id", "dimension"])
    op.create_index("ix_point_user_date", "point_events", ["user_id", "created_at"])

    # ── user_point_balances (三维积分余额) ──
    op.create_table(
        "user_point_balances",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("growth", sa.Integer, server_default="0"),
        sa.Column("contribution", sa.Integer, server_default="0"),
        sa.Column("influence", sa.Integer, server_default="0"),
        sa.Column("total", sa.Integer, server_default="0"),
        sa.Column("streak_days", sa.Integer, server_default="0"),
        sa.Column("longest_streak", sa.Integer, server_default="0"),
        sa.Column("last_checkin_date", sa.DateTime, nullable=True),
        sa.Column("tasks_completed_total", sa.Integer, server_default="0"),
        sa.Column("assessments_completed", sa.Integer, server_default="0"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── incentive_rewards (激励奖励定义) ──
    op.create_table(
        "incentive_rewards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("reward_type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("icon", sa.String(10)),
        sa.Column("unlock_dimension", sa.String(15)),
        sa.Column("unlock_threshold", sa.Integer),
        sa.Column("unlock_growth_level", sa.String(4)),
        sa.Column("rx_effect", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
    )

    # ── user_rewards (用户已获得奖励) ──
    op.create_table(
        "user_rewards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reward_id", sa.Integer, sa.ForeignKey("incentive_rewards.id"), nullable=False),
        sa.Column("earned_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "reward_id", name="uq_user_reward"),
    )

    # ── assessment_sessions (渐进式评估会话) ──
    op.create_table(
        "assessment_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(15), nullable=False, server_default="in_progress"),
        sa.Column("completed_batches", sa.JSON),
        sa.Column("pending_batches", sa.JSON),
        sa.Column("total_questions_answered", sa.Integer, server_default="0"),
        sa.Column("total_questions", sa.Integer, server_default="176"),
        sa.Column("partial_results", sa.JSON),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_activity", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_assess_session_user", "assessment_sessions", ["user_id", "status"])

    # ── batch_answers (单批次答题记录) ──
    op.create_table(
        "batch_answers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("assessment_sessions.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("batch_id", sa.String(30), nullable=False),
        sa.Column("questionnaire", sa.String(10), nullable=False),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("scores", sa.JSON, nullable=True),
        sa.Column("duration_seconds", sa.Integer),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_batch_session", "batch_answers", ["session_id", "batch_id"])

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
        "user_rewards", "incentive_rewards", "user_point_balances", "point_events",
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
