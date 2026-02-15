"""033 - V4.0 Stage Engine + Governance Tracking

- Add stage tracking columns to journey_states
- Create stage_transition_logs table
- Create responsibility_metrics table
- Create anti_cheat_events table
- Create governance_violations table

Revision ID: 033
Revises: 032
"""
from alembic import op
import sqlalchemy as sa

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Add stage tracking columns to journey_states ──
    cols_to_add = [
        ("stage_entered_at", "TIMESTAMP", "NOW()"),
        ("stability_start_date", "DATE", None),
        ("stability_days", "INTEGER", "0"),
        ("interruption_count", "INTEGER", "0"),
        ("last_interruption_at", "TIMESTAMP", None),
        ("stage_transition_count", "INTEGER", "0"),
    ]
    for col_name, col_type, default in cols_to_add:
        default_clause = f" DEFAULT {default}" if default else ""
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='journey_states' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE journey_states ADD COLUMN {col_name} {col_type}{default_clause};
                END IF;
            END $$;
        """)

    # ── 2. Create stage_transition_logs table ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS stage_transition_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            from_stage VARCHAR(30) NOT NULL,
            to_stage VARCHAR(30) NOT NULL,
            reason VARCHAR(100),
            triggered_by VARCHAR(30) NOT NULL DEFAULT 'system',
            triggered_by_user_id INTEGER,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_stl_user_id ON stage_transition_logs(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_stl_created ON stage_transition_logs(created_at);")

    # ── 3. Create responsibility_metrics table ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS responsibility_metrics (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            metric_code VARCHAR(20) NOT NULL,
            metric_value FLOAT NOT NULL DEFAULT 0.0,
            threshold_value FLOAT,
            status VARCHAR(20) NOT NULL DEFAULT 'healthy',
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            details JSONB DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, metric_code, period_start)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_rm_user_id ON responsibility_metrics(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rm_code ON responsibility_metrics(metric_code);")

    # ── 4. Create anti_cheat_events table ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS anti_cheat_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            strategy VARCHAR(10) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            details JSONB DEFAULT '{}',
            action_taken VARCHAR(50),
            resolved BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ace_user ON anti_cheat_events(user_id);")

    # ── 5. Create governance_violations table ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS governance_violations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            violation_type VARCHAR(30) NOT NULL,
            severity VARCHAR(20) NOT NULL DEFAULT 'light',
            description TEXT,
            point_penalty INTEGER NOT NULL DEFAULT 0,
            action_taken VARCHAR(50),
            protection_until DATE,
            recovery_path TEXT,
            resolved BOOLEAN NOT NULL DEFAULT FALSE,
            resolved_by INTEGER,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_gv_user ON governance_violations(user_id);")

    # ── 6. Create dual_track_status table for promotion state machine ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS dual_track_status (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            target_level INTEGER NOT NULL,
            points_track_passed BOOLEAN NOT NULL DEFAULT FALSE,
            growth_track_passed BOOLEAN NOT NULL DEFAULT FALSE,
            status VARCHAR(30) NOT NULL DEFAULT 'normal_growth',
            gap_analysis JSONB DEFAULT '{}',
            points_checked_at TIMESTAMP,
            growth_checked_at TIMESTAMP,
            ceremony_triggered_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, target_level)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_dts_user ON dual_track_status(user_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dual_track_status;")
    op.execute("DROP TABLE IF EXISTS governance_violations;")
    op.execute("DROP TABLE IF EXISTS anti_cheat_events;")
    op.execute("DROP TABLE IF EXISTS responsibility_metrics;")
    op.execute("DROP TABLE IF EXISTS stage_transition_logs;")
    for col in ["stage_entered_at", "stability_start_date", "stability_days",
                "interruption_count", "last_interruption_at", "stage_transition_count"]:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='journey_states' AND column_name='{col}'
                ) THEN
                    ALTER TABLE journey_states DROP COLUMN {col};
                END IF;
            END $$;
        """)
