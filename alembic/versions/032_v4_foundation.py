"""migration_032_v4_foundation

V4.0 Platform Restructuring — Sprint 0 Foundation
  1. New enums: agency_mode_enum, journey_stage_v4_enum
  2. New table: journey_states (user lifecycle tracking with agency/trust)
  3. New table: trust_score_logs (trust signal history)
  4. New table: agency_score_logs (agency signal history)
  5. ALTER users: +agency_mode, +agency_score, +trust_score, +coach_intent,
                  +conversion_type, +conversion_source
  6. ALTER behavioral_profiles: +agency_mode, +agency_score, +trust_score
  7. ALTER content_items: +level (content gating L0-L5)

Revision ID: 032
Revises: 031 (expert_self_registration)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers
revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create enums ──────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agency_mode_enum AS ENUM ('passive', 'transitional', 'active');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE journey_stage_v4_enum AS ENUM (
                's0_authorization', 's1_awareness', 's2_trial',
                's3_pathway', 's4_internalization', 's5_graduation'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── 2. journey_states ────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS journey_states (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            journey_stage   journey_stage_v4_enum NOT NULL DEFAULT 's0_authorization',

            -- Agency mode (3-state model)
            agency_mode     agency_mode_enum NOT NULL DEFAULT 'passive',
            agency_score    FLOAT NOT NULL DEFAULT 0.0,
            agency_signals  JSONB DEFAULT '{}',
            coach_override_agency agency_mode_enum DEFAULT NULL,

            -- Trust score
            trust_score     FLOAT NOT NULL DEFAULT 0.0,
            trust_signals   JSONB DEFAULT '{}',

            -- Conversion tracking
            conversion_type   VARCHAR(30) DEFAULT NULL,   -- curiosity/time/coach_referred
            conversion_source VARCHAR(30) DEFAULT NULL,   -- self/community/institution/paid

            -- Lifecycle timestamps
            activated_at    TIMESTAMP DEFAULT NULL,       -- Observer→Grower
            graduated_at    TIMESTAMP DEFAULT NULL,       -- S5 graduation

            -- Observer trial tracking
            observer_dialog_count INTEGER NOT NULL DEFAULT 0,
            observer_last_dialog_date DATE DEFAULT NULL,

            -- Timestamps
            created_at      TIMESTAMP NOT NULL DEFAULT now(),
            updated_at      TIMESTAMP NOT NULL DEFAULT now(),

            CONSTRAINT uq_journey_user UNIQUE (user_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_journey_user ON journey_states(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_journey_stage ON journey_states(journey_stage);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_journey_agency ON journey_states(agency_mode);")

    # ── 3. trust_score_logs ──────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS trust_score_logs (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            signal_name     VARCHAR(50) NOT NULL,
            signal_value    FLOAT NOT NULL DEFAULT 0.0,
            weight          FLOAT NOT NULL DEFAULT 0.0,
            computed_score  FLOAT NOT NULL DEFAULT 0.0,
            source          VARCHAR(50) DEFAULT 'system',
            context         JSONB DEFAULT '{}',
            created_at      TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_trust_log_user ON trust_score_logs(user_id, created_at);")

    # ── 4. agency_score_logs ─────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS agency_score_logs (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            signal_name     VARCHAR(50) NOT NULL,
            signal_value    FLOAT NOT NULL DEFAULT 0.0,
            weight          FLOAT NOT NULL DEFAULT 0.0,
            computed_score  FLOAT NOT NULL DEFAULT 0.0,
            source          VARCHAR(50) DEFAULT 'system',
            context         JSONB DEFAULT '{}',
            created_at      TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_agency_log_user ON agency_score_logs(user_id, created_at);")

    # ── 5. ALTER users ───────────────────────────────────
    for col_sql in [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS agency_mode VARCHAR(20) DEFAULT 'passive'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS agency_score FLOAT DEFAULT 0.0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS trust_score FLOAT DEFAULT 0.0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS coach_intent BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS conversion_type VARCHAR(30) DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS conversion_source VARCHAR(30) DEFAULT NULL",
    ]:
        op.execute(col_sql)

    # ── 6. ALTER behavioral_profiles ─────────────────────
    for col_sql in [
        "ALTER TABLE behavioral_profiles ADD COLUMN IF NOT EXISTS agency_mode VARCHAR(20) DEFAULT 'passive'",
        "ALTER TABLE behavioral_profiles ADD COLUMN IF NOT EXISTS agency_score FLOAT DEFAULT 0.0",
        "ALTER TABLE behavioral_profiles ADD COLUMN IF NOT EXISTS trust_score FLOAT DEFAULT 0.0",
    ]:
        op.execute(col_sql)

    # ── 7. ALTER content_items: +level (content gating) ──
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 0")

    # ── 8. Create trigger for journey_states updated_at ──
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_journey_states_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_journey_states_updated ON journey_states;
        CREATE TRIGGER trg_journey_states_updated
            BEFORE UPDATE ON journey_states
            FOR EACH ROW EXECUTE FUNCTION trg_journey_states_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_journey_states_updated ON journey_states;")
    op.execute("DROP FUNCTION IF EXISTS trg_journey_states_updated_at();")
    op.execute("ALTER TABLE content_items DROP COLUMN IF EXISTS level;")
    for col in ['agency_mode', 'agency_score', 'trust_score']:
        op.execute(f"ALTER TABLE behavioral_profiles DROP COLUMN IF EXISTS {col};")
    for col in ['agency_mode', 'agency_score', 'trust_score', 'coach_intent', 'conversion_type', 'conversion_source']:
        op.execute(f"ALTER TABLE users DROP COLUMN IF EXISTS {col};")
    op.execute("DROP TABLE IF EXISTS agency_score_logs;")
    op.execute("DROP TABLE IF EXISTS trust_score_logs;")
    op.execute("DROP TABLE IF EXISTS journey_states;")
    op.execute("DROP TYPE IF EXISTS journey_stage_v4_enum;")
    op.execute("DROP TYPE IF EXISTS agency_mode_enum;")
