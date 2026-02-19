"""
Alembic Migration 044 — V5.0 飞轮数据库表

新增 7 张表:
  1. observer_quota_logs  — Observer试用墙额度日志
  2. task_checkins        — Grower任务打卡记录
  3. user_streaks         — 用户连续打卡天数
  4. coach_review_queue   — Coach审核队列(含AI预填)
  5. coach_review_logs    — Coach审核效率日志
  6. expert_audit_records — Expert审核裁决记录
  7. system_alerts        — Admin指挥中心告警

扩展 2 张表:
  - daily_tasks: +input_mode, +quick_label, +agent_id, +source
  - users: +union_id, +wx_openid, +wx_miniprogram_openid, +preferred_channel, +growth_points

Revision ID: 044
Revises: 043
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY


revision = "044"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    def _table_exists(name, schema="public"):
        r = conn.execute(sa.text(
            "SELECT EXISTS(SELECT 1 FROM pg_tables WHERE schemaname=:s AND tablename=:t)"
        ), {"s": schema, "t": name})
        return r.scalar()

    def _column_exists(table, col):
        r = conn.execute(sa.text(
            "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND column_name=:c)"
        ), {"t": table, "c": col})
        return r.scalar()

    # ── 0a. behavior_prescriptions (prerequisite for daily_tasks FK) ──
    if not _table_exists("behavior_prescriptions"):
        op.execute("""
        CREATE TABLE behavior_prescriptions (
            id VARCHAR(80) PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_behavior VARCHAR(200) NOT NULL,
            frequency_dose VARCHAR(100),
            time_place VARCHAR(200),
            trigger_cue VARCHAR(200),
            obstacle_plan TEXT,
            support_resource TEXT,
            domain VARCHAR(30),
            difficulty_level VARCHAR(20) DEFAULT 'easy',
            cultivation_stage VARCHAR(30) DEFAULT 'startup',
            status VARCHAR(20) DEFAULT 'draft',
            expires_at TIMESTAMP,
            approved_by_review VARCHAR(80),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
        """)
        op.execute("CREATE INDEX IF NOT EXISTS idx_bp_user ON behavior_prescriptions(user_id);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_bp_status ON behavior_prescriptions(status);")

    # ── 0b. daily_tasks (prerequisite — no prior migration creates it) ──
    if not _table_exists("daily_tasks"):
        op.execute("""
        CREATE TABLE daily_tasks (
            id VARCHAR(80) PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task_date DATE NOT NULL,
            order_num INTEGER DEFAULT 0,
            title VARCHAR(200) NOT NULL,
            tag VARCHAR(20),
            tag_color VARCHAR(10),
            time_hint VARCHAR(100),
            input_mode VARCHAR(20),
            quick_label VARCHAR(20) DEFAULT '打卡',
            source VARCHAR(20) DEFAULT 'rx',
            agent_id VARCHAR(50),
            rx_id VARCHAR(80) REFERENCES behavior_prescriptions(id),
            done BOOLEAN DEFAULT false,
            done_time TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        );
        """)
        op.execute("CREATE INDEX IF NOT EXISTS idx_dt_user_date ON daily_tasks(user_id, task_date);")

    # ── 1. observer_quota_logs ──
    if not _table_exists("observer_quota_logs"):
        op.create_table(
            "observer_quota_logs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("quota_type", sa.String(20), nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("idx_observer_quota_user_date", "observer_quota_logs", ["user_id", "created_at"])

    # ── 2. task_checkins ──
    if not _table_exists("task_checkins"):
        op.create_table(
            "task_checkins",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("task_id", sa.String(50), nullable=False),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("note", sa.Text, nullable=True),
            sa.Column("photo_url", sa.String(500), nullable=True),
            sa.Column("value", sa.Float, nullable=True),
            sa.Column("voice_url", sa.String(500), nullable=True),
            sa.Column("points_earned", sa.Integer, server_default="0"),
            sa.Column("checked_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("idx_checkin_user_date", "task_checkins", ["user_id", "checked_at"])
        op.create_index("idx_checkin_task", "task_checkins", ["task_id"])

    # ── 3. user_streaks ──
    if not _table_exists("user_streaks"):
        op.create_table(
            "user_streaks",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("current_streak", sa.Integer, server_default="0", nullable=False),
            sa.Column("longest_streak", sa.Integer, server_default="0", nullable=False),
            sa.Column("last_checkin_date", sa.Date, nullable=True),
            sa.Column("updated_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        )

    # ── 4. coach_review_queue ──
    if not _table_exists("coach_review_queue"):
        op.create_table(
            "coach_review_queue",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("coach_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("type", sa.String(20), nullable=False),
            sa.Column("priority", sa.String(10), server_default="normal", nullable=False),
            sa.Column("status", sa.String(20), server_default="pending", nullable=False),
            sa.Column("ai_summary", sa.Text, nullable=True),
            sa.Column("rx_fields_json", JSONB, nullable=True),
            sa.Column("ai_draft", sa.Text, nullable=True),
            sa.Column("push_type", sa.String(50), nullable=True),
            sa.Column("push_content", sa.Text, nullable=True),
            sa.Column("review_note", sa.Text, nullable=True),
            sa.Column("edited_content", sa.Text, nullable=True),
            sa.Column("edited_rx_json", JSONB, nullable=True),
            sa.Column("reviewed_at", sa.DateTime, nullable=True),
            sa.Column("elapsed_seconds", sa.Integer, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
            sa.Column("picked_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_review_coach_status", "coach_review_queue", ["coach_id", "status"])
        op.create_index("idx_review_priority", "coach_review_queue", ["priority", "created_at"])
        op.create_index("idx_review_student", "coach_review_queue", ["student_id", "created_at"])

    # ── 5. coach_review_logs ──
    if not _table_exists("coach_review_logs"):
        op.create_table(
            "coach_review_logs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("coach_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("review_id", sa.String(50), nullable=False),
            sa.Column("action", sa.String(20), nullable=False),
            sa.Column("elapsed_seconds", sa.Integer, nullable=True),
            sa.Column("reviewed_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("idx_review_log_coach_date", "coach_review_logs", ["coach_id", "reviewed_at"])

    # ── 6. expert_audit_records ──
    if not _table_exists("expert_audit_records"):
        op.create_table(
            "expert_audit_records",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("expert_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("audit_type", sa.String(30), nullable=False),
            sa.Column("agent_id", sa.String(50), nullable=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("risk_level", sa.String(10), nullable=True),
            sa.Column("content_snapshot", JSONB, nullable=False),
            sa.Column("safety_flags", JSONB, server_default=sa.text("'[]'::jsonb")),
            sa.Column("verdict", sa.String(10), nullable=True),
            sa.Column("score", sa.SmallInteger, nullable=True),
            sa.Column("issues", ARRAY(sa.Text), nullable=True),
            sa.Column("note", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
            sa.Column("reviewed_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_audit_expert_date", "expert_audit_records", ["expert_id", "created_at"])
        op.create_index("idx_audit_type_risk", "expert_audit_records", ["audit_type", "risk_level"])
        op.create_index("idx_audit_agent", "expert_audit_records", ["agent_id"])

    # ── 7. system_alerts ──
    if not _table_exists("system_alerts"):
        op.create_table(
            "system_alerts",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("level", sa.String(10), nullable=False),
            sa.Column("message", sa.Text, nullable=False),
            sa.Column("source", sa.String(50), nullable=True),
            sa.Column("status", sa.String(10), server_default="active", nullable=False),
            sa.Column("dismissed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("dismissed_at", sa.DateTime, nullable=True),
            sa.Column("auto_resolved", sa.Boolean, server_default="false"),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("idx_alert_status", "system_alerts", ["status", "created_at"])

    # ── 8. 扩展 daily_tasks 表 ──
    for col_name, col_sql in [
        ("input_mode", "VARCHAR(20)"),
        ("quick_label", "VARCHAR(20) DEFAULT '打卡'"),
        ("agent_id", "VARCHAR(50)"),
        ("source", "VARCHAR(20) DEFAULT 'rx'"),
    ]:
        op.execute(f"ALTER TABLE daily_tasks ADD COLUMN IF NOT EXISTS {col_name} {col_sql};")

    # ── 9. 扩展 users 表 ──
    for col_name, col_sql in [
        ("union_id", "VARCHAR(100)"),
        ("wx_openid", "VARCHAR(100)"),
        ("wx_miniprogram_openid", "VARCHAR(100)"),
        ("preferred_channel", "VARCHAR(20) DEFAULT 'app'"),
        ("growth_points", "INTEGER DEFAULT 0"),
    ]:
        op.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_sql};")

    # 微信字段唯一索引 (partial - WHERE NOT NULL)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_union_id ON users(union_id) WHERE union_id IS NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_wx_openid ON users(wx_openid) WHERE wx_openid IS NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_wx_mini_openid ON users(wx_miniprogram_openid) WHERE wx_miniprogram_openid IS NOT NULL")


def downgrade():
    # 微信唯一索引
    op.execute("DROP INDEX IF EXISTS idx_users_wx_mini_openid")
    op.execute("DROP INDEX IF EXISTS idx_users_wx_openid")
    op.execute("DROP INDEX IF EXISTS idx_users_union_id")

    # users 扩展列
    op.drop_column("users", "growth_points")
    op.drop_column("users", "preferred_channel")
    op.drop_column("users", "wx_miniprogram_openid")
    op.drop_column("users", "wx_openid")
    op.drop_column("users", "union_id")

    # daily_tasks 扩展列
    op.drop_column("daily_tasks", "source")
    op.drop_column("daily_tasks", "agent_id")
    op.drop_column("daily_tasks", "quick_label")
    op.drop_column("daily_tasks", "input_mode")

    # 7 张新表 (逆序)
    op.drop_table("system_alerts")
    op.drop_table("expert_audit_records")
    op.drop_table("coach_review_logs")
    op.drop_table("coach_review_queue")
    op.drop_table("user_streaks")
    op.drop_table("task_checkins")
    op.drop_table("observer_quota_logs")
