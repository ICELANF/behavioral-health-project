"""user_weekly_reports table

Revision ID: 049
Revises: 048
"""
from alembic import op
import sqlalchemy as sa

revision = "049"
down_revision = "048"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_weekly_reports (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            week_start  DATE NOT NULL,
            week_end    DATE NOT NULL,
            tasks_total       INTEGER NOT NULL DEFAULT 0,
            tasks_completed   INTEGER NOT NULL DEFAULT 0,
            completion_pct    REAL NOT NULL DEFAULT 0,
            checkin_count     INTEGER NOT NULL DEFAULT 0,
            learning_minutes  INTEGER NOT NULL DEFAULT 0,
            points_earned     INTEGER NOT NULL DEFAULT 0,
            activity_count    INTEGER NOT NULL DEFAULT 0,
            streak_days       INTEGER NOT NULL DEFAULT 0,
            highlights        JSONB DEFAULT '[]'::jsonb,
            suggestions       JSONB DEFAULT '[]'::jsonb,
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
            UNIQUE (user_id, week_start)
        );
        CREATE INDEX IF NOT EXISTS idx_uwr_user_week ON user_weekly_reports (user_id, week_start DESC);
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS user_weekly_reports;")
