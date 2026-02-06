"""Full schema - explicit table definitions for all models

Revision ID: 002
Revises: 001
Create Date: 2026-02-06

This migration creates all tables explicitly instead of using create_all,
making it production-safe and auditable.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with explicit column definitions."""
    conn = op.get_bind()

    # Check which tables already exist, only create missing ones
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # --- users ---
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
            sa.Column("email", sa.String(100), unique=True, nullable=False, index=True),
            sa.Column("phone", sa.String(20), unique=True, nullable=True),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_verified", sa.Boolean(), default=False),
            sa.Column("role", sa.String(20), nullable=False, default="patient"),
            sa.Column("full_name", sa.String(100), nullable=True),
            sa.Column("date_of_birth", sa.DateTime(), nullable=True),
            sa.Column("gender", sa.String(10), nullable=True),
            sa.Column("profile", sa.JSON(), nullable=True),
            sa.Column("adherence_rate", sa.Float(), default=0.0),
            sa.Column("last_assessment_date", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("last_login_at", sa.DateTime(), nullable=True),
        )

    # --- assessments ---
    if "assessments" not in existing_tables:
        op.create_table(
            "assessments",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("assessment_id", sa.String(50), unique=True, nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("text_content", sa.Text(), nullable=True),
            sa.Column("glucose_values", sa.JSON(), nullable=True),
            sa.Column("hrv_values", sa.JSON(), nullable=True),
            sa.Column("activity_data", sa.JSON(), nullable=True),
            sa.Column("sleep_data", sa.JSON(), nullable=True),
            sa.Column("user_profile_snapshot", sa.JSON(), nullable=True),
            sa.Column("risk_level", sa.String(10), nullable=False),
            sa.Column("risk_score", sa.Float(), nullable=False),
            sa.Column("primary_concern", sa.String(200), nullable=True),
            sa.Column("urgency", sa.String(20), nullable=True),
            sa.Column("severity_distribution", sa.JSON(), nullable=True),
            sa.Column("reasoning", sa.Text(), nullable=True),
            sa.Column("primary_agent", sa.String(50), nullable=False),
            sa.Column("secondary_agents", sa.JSON(), nullable=True),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("response_time", sa.String(50), nullable=True),
            sa.Column("routing_reasoning", sa.Text(), nullable=True),
            sa.Column("recommended_actions", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(20), default="pending"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("context", sa.JSON(), nullable=True),
        )

    # --- trigger_records ---
    if "trigger_records" not in existing_tables:
        op.create_table(
            "trigger_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), nullable=False, index=True),
            sa.Column("tag_id", sa.String(50), nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("category", sa.String(20), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False, index=True),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- interventions ---
    if "interventions" not in existing_tables:
        op.create_table(
            "interventions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), nullable=False, index=True),
            sa.Column("agent_type", sa.String(50), nullable=False),
            sa.Column("intervention_type", sa.String(50), nullable=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("actions", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(20), default="pending"),
            sa.Column("user_feedback", sa.Text(), nullable=True),
            sa.Column("feedback_score", sa.Integer(), nullable=True),
            sa.Column("completed", sa.Boolean(), default=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("sent_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )

    # --- user_sessions ---
    if "user_sessions" not in existing_tables:
        op.create_table(
            "user_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(100), unique=True, nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("token", sa.String(500), nullable=True),
            sa.Column("refresh_token", sa.String(500), nullable=True),
            sa.Column("ip_address", sa.String(50), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.Column("device_info", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
            sa.Column("last_activity_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- health_data ---
    if "health_data" not in existing_tables:
        op.create_table(
            "health_data",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("data_type", sa.String(50), nullable=False, index=True),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("values", sa.JSON(), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("source", sa.String(50), nullable=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- chat_sessions ---
    if "chat_sessions" not in existing_tables:
        op.create_table(
            "chat_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(100), unique=True, nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("title", sa.String(200), nullable=True),
            sa.Column("model", sa.String(50), default="qwen2.5:0.5b"),
            sa.Column("is_active", sa.Boolean(), default=True, index=True),
            sa.Column("message_count", sa.Integer(), default=0),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- chat_messages ---
    if "chat_messages" not in existing_tables:
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id"), nullable=False, index=True),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("model", sa.String(50), nullable=True),
            sa.Column("tokens_used", sa.Integer(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- user_devices ---
    if "user_devices" not in existing_tables:
        op.create_table(
            "user_devices",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), unique=True, nullable=False, index=True),
            sa.Column("device_type", sa.String(20), nullable=False),
            sa.Column("manufacturer", sa.String(50), nullable=True),
            sa.Column("model", sa.String(100), nullable=True),
            sa.Column("firmware_version", sa.String(50), nullable=True),
            sa.Column("serial_number", sa.String(100), nullable=True),
            sa.Column("status", sa.String(20), default="connected"),
            sa.Column("battery_level", sa.Integer(), nullable=True),
            sa.Column("auth_token", sa.Text(), nullable=True),
            sa.Column("auth_expires_at", sa.DateTime(), nullable=True),
            sa.Column("last_sync_at", sa.DateTime(), nullable=True),
            sa.Column("sync_cursor", sa.String(200), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- glucose_readings ---
    if "glucose_readings" not in existing_tables:
        op.create_table(
            "glucose_readings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), nullable=True, index=True),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(10), default="mmol/L"),
            sa.Column("trend", sa.String(20), nullable=True),
            sa.Column("trend_rate", sa.Float(), nullable=True),
            sa.Column("source", sa.String(20), default="manual"),
            sa.Column("meal_tag", sa.String(20), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- heart_rate_readings ---
    if "heart_rate_readings" not in existing_tables:
        op.create_table(
            "heart_rate_readings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("hr", sa.Integer(), nullable=False),
            sa.Column("activity_type", sa.String(20), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- hrv_readings ---
    if "hrv_readings" not in existing_tables:
        op.create_table(
            "hrv_readings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("sdnn", sa.Float(), nullable=True),
            sa.Column("rmssd", sa.Float(), nullable=True),
            sa.Column("lf", sa.Float(), nullable=True),
            sa.Column("hf", sa.Float(), nullable=True),
            sa.Column("lf_hf_ratio", sa.Float(), nullable=True),
            sa.Column("stress_score", sa.Float(), nullable=True),
            sa.Column("recovery_score", sa.Float(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- sleep_records ---
    if "sleep_records" not in existing_tables:
        op.create_table(
            "sleep_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("sleep_date", sa.String(10), nullable=False, index=True),
            sa.Column("sleep_start", sa.DateTime(), nullable=True),
            sa.Column("sleep_end", sa.DateTime(), nullable=True),
            sa.Column("total_duration_min", sa.Integer(), nullable=True),
            sa.Column("awake_min", sa.Integer(), default=0),
            sa.Column("light_min", sa.Integer(), default=0),
            sa.Column("deep_min", sa.Integer(), default=0),
            sa.Column("rem_min", sa.Integer(), default=0),
            sa.Column("sleep_score", sa.Integer(), nullable=True),
            sa.Column("efficiency", sa.Float(), nullable=True),
            sa.Column("awakenings", sa.Integer(), default=0),
            sa.Column("onset_latency_min", sa.Integer(), nullable=True),
            sa.Column("avg_spo2", sa.Float(), nullable=True),
            sa.Column("min_spo2", sa.Float(), nullable=True),
            sa.Column("stages_data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- activity_records ---
    if "activity_records" not in existing_tables:
        op.create_table(
            "activity_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("activity_date", sa.String(10), nullable=False, index=True),
            sa.Column("steps", sa.Integer(), default=0),
            sa.Column("distance_m", sa.Integer(), default=0),
            sa.Column("floors_climbed", sa.Integer(), default=0),
            sa.Column("calories_total", sa.Integer(), default=0),
            sa.Column("calories_active", sa.Integer(), default=0),
            sa.Column("sedentary_min", sa.Integer(), default=0),
            sa.Column("light_active_min", sa.Integer(), default=0),
            sa.Column("moderate_active_min", sa.Integer(), default=0),
            sa.Column("vigorous_active_min", sa.Integer(), default=0),
            sa.Column("hourly_data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- workout_records ---
    if "workout_records" not in existing_tables:
        op.create_table(
            "workout_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("workout_type", sa.String(50), nullable=False),
            sa.Column("start_time", sa.DateTime(), nullable=False),
            sa.Column("end_time", sa.DateTime(), nullable=True),
            sa.Column("duration_min", sa.Integer(), nullable=True),
            sa.Column("distance_m", sa.Integer(), nullable=True),
            sa.Column("calories", sa.Integer(), nullable=True),
            sa.Column("avg_hr", sa.Integer(), nullable=True),
            sa.Column("max_hr", sa.Integer(), nullable=True),
            sa.Column("avg_pace", sa.String(20), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("gps_data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- vital_signs ---
    if "vital_signs" not in existing_tables:
        op.create_table(
            "vital_signs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("data_type", sa.String(20), nullable=False),
            sa.Column("weight_kg", sa.Float(), nullable=True),
            sa.Column("bmi", sa.Float(), nullable=True),
            sa.Column("body_fat_percent", sa.Float(), nullable=True),
            sa.Column("muscle_mass_kg", sa.Float(), nullable=True),
            sa.Column("water_percent", sa.Float(), nullable=True),
            sa.Column("visceral_fat", sa.Integer(), nullable=True),
            sa.Column("systolic", sa.Integer(), nullable=True),
            sa.Column("diastolic", sa.Integer(), nullable=True),
            sa.Column("pulse", sa.Integer(), nullable=True),
            sa.Column("temperature", sa.Float(), nullable=True),
            sa.Column("spo2", sa.Float(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- behavior_audit_logs ---
    if "behavior_audit_logs" not in existing_tables:
        op.create_table(
            "behavior_audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.String(50), nullable=False, index=True),
            sa.Column("from_stage", sa.String(10), nullable=False),
            sa.Column("to_stage", sa.String(10), nullable=False),
            sa.Column("narrative", sa.Text(), nullable=True),
            sa.Column("source_ui", sa.String(20), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # --- behavior_history ---
    if "behavior_history" not in existing_tables:
        op.create_table(
            "behavior_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.String(50), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("from_stage", sa.String(10), nullable=False),
            sa.Column("to_stage", sa.String(10), nullable=False),
            sa.Column("is_transition", sa.Boolean(), default=False),
            sa.Column("belief_score", sa.Float(), nullable=True),
            sa.Column("narrative_sent", sa.Text(), nullable=True),
        )

    # --- behavior_traces ---
    if "behavior_traces" not in existing_tables:
        op.create_table(
            "behavior_traces",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.String(50), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("from_stage", sa.String(10), nullable=False),
            sa.Column("to_stage", sa.String(10), nullable=False),
            sa.Column("is_transition", sa.Boolean(), default=False),
            sa.Column("belief_score", sa.Float(), nullable=True),
            sa.Column("action_count", sa.Integer(), nullable=True),
            sa.Column("narrative_sent", sa.Text(), nullable=True),
            sa.Column("source_ui", sa.String(20), nullable=True),
        )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    tables = [
        "behavior_traces", "behavior_history", "behavior_audit_logs",
        "vital_signs", "workout_records", "activity_records",
        "sleep_records", "hrv_readings", "heart_rate_readings",
        "glucose_readings", "user_devices",
        "chat_messages", "chat_sessions",
        "health_data", "user_sessions",
        "interventions", "trigger_records", "assessments",
        "users",
    ]
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = inspector.get_table_names()
    for t in tables:
        if t in existing:
            op.drop_table(t)
