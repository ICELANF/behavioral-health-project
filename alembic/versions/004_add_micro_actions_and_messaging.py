"""Add micro_action_tasks, micro_action_logs, reminders, coach_messages tables

Revision ID: 004
Revises: 003
Create Date: 2026-02-06

Adds tables for:
- micro_action_tasks: 微行动任务
- micro_action_logs: 微行动完成日志
- reminders: 提醒
- coach_messages: 教练消息
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create micro_action_tasks, micro_action_logs, reminders, coach_messages tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ---- micro_action_tasks ----
    if "micro_action_tasks" not in existing_tables:
        op.create_table(
            "micro_action_tasks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("domain", sa.String(30), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("difficulty", sa.String(20), server_default="easy"),
            sa.Column("source", sa.String(30), server_default="intervention_plan"),
            sa.Column("source_id", sa.String(50), nullable=True),
            sa.Column("status", sa.String(20), server_default="pending"),
            sa.Column("scheduled_date", sa.String(10), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("idx_micro_task_user_date", "micro_action_tasks", ["user_id", "scheduled_date"])
        op.create_index("idx_micro_task_status", "micro_action_tasks", ["status"])
        op.create_index("idx_micro_task_domain", "micro_action_tasks", ["domain"])

    # ---- micro_action_logs ----
    if "micro_action_logs" not in existing_tables:
        op.create_table(
            "micro_action_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("task_id", sa.Integer(), sa.ForeignKey("micro_action_tasks.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("action", sa.String(20), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("mood_score", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_micro_log_user_created", "micro_action_logs", ["user_id", "created_at"])
        op.create_index("idx_micro_log_task", "micro_action_logs", ["task_id"])

    # ---- reminders ----
    if "reminders" not in existing_tables:
        op.create_table(
            "reminders",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("type", sa.String(30), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("cron_expr", sa.String(50), nullable=True),
            sa.Column("next_fire_at", sa.DateTime(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="1"),
            sa.Column("source", sa.String(20), server_default="self"),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("idx_reminder_user_active", "reminders", ["user_id", "is_active"])
        op.create_index("idx_reminder_next_fire", "reminders", ["next_fire_at"])

    # ---- coach_messages ----
    if "coach_messages" not in existing_tables:
        op.create_table(
            "coach_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("coach_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("message_type", sa.String(20), server_default="text"),
            sa.Column("is_read", sa.Boolean(), server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_coach_msg_student_read", "coach_messages", ["student_id", "is_read"])
        op.create_index("idx_coach_msg_coach_student", "coach_messages", ["coach_id", "student_id"])


def downgrade() -> None:
    """Drop all 4 new tables."""
    for table in ["coach_messages", "reminders", "micro_action_logs", "micro_action_tasks"]:
        try:
            op.drop_table(table)
        except Exception:
            pass
