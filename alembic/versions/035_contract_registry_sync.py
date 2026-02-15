"""
035 — Contract Registry Sync (契约注册表对齐)

基于 V4.0 契约注册表 xlsx 的 gap analysis:
1. ies_scores — IES 干预效果评分持久化
2. ies_decision_log — IES 决策追踪日志
3. user_contracts — 用户契约生命周期追踪
4. ethical_declarations — 伦理声明存储 (5条Coach / 7条Promoter)
5. device_alerts +risk_level 列
6. assessment_sessions +expires_at 列

Revision ID: 035
Revises: 034
"""
from alembic import op
import sqlalchemy as sa

revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. IES Scores ─────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS ies_scores (
        id              SERIAL PRIMARY KEY,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        agent_type      VARCHAR(50),
        period_start    DATE NOT NULL,
        period_end      DATE NOT NULL,
        -- 4-component formula: 0.4×completion + 0.2×activity + 0.25×progression - 0.15×resistance
        completion_rate FLOAT NOT NULL DEFAULT 0.0,
        activity_rate   FLOAT NOT NULL DEFAULT 0.0,
        progression_delta FLOAT NOT NULL DEFAULT 0.0,
        resistance_index FLOAT NOT NULL DEFAULT 0.0,
        ies_score       FLOAT NOT NULL DEFAULT 0.0,
        interpretation  VARCHAR(30) NOT NULL DEFAULT 'no_change',
        details         JSONB DEFAULT '{}',
        created_at      TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_ies_scores_user ON ies_scores(user_id, period_end);
    CREATE INDEX IF NOT EXISTS idx_ies_scores_agent ON ies_scores(agent_type, period_end);
    """)

    # ── 2. IES Decision Log ───────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS ies_decision_log (
        id              SERIAL PRIMARY KEY,
        ies_score_id    INTEGER REFERENCES ies_scores(id),
        user_id         INTEGER NOT NULL REFERENCES users(id),
        decision_type   VARCHAR(30) NOT NULL,
        old_value       VARCHAR(100),
        new_value       VARCHAR(100),
        reason          TEXT,
        auto_applied    BOOLEAN NOT NULL DEFAULT FALSE,
        created_at      TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_ies_decision_user ON ies_decision_log(user_id, created_at);
    """)

    # ── 3. User Contracts ─────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS user_contracts (
        id              SERIAL PRIMARY KEY,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        contract_type   VARCHAR(30) NOT NULL,
        role_at_signing VARCHAR(20) NOT NULL,
        level_at_signing INTEGER NOT NULL DEFAULT 0,
        content_snapshot JSONB DEFAULT '{}',
        signed_at       TIMESTAMP NOT NULL DEFAULT NOW(),
        expires_at      TIMESTAMP,
        status          VARCHAR(20) NOT NULL DEFAULT 'active',
        renewed_from_id INTEGER REFERENCES user_contracts(id),
        created_at      TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_user_contracts_user ON user_contracts(user_id, status);
    CREATE INDEX IF NOT EXISTS idx_user_contracts_type ON user_contracts(contract_type, status);
    """)

    # ── 4. Ethical Declarations ───────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS ethical_declarations (
        id              SERIAL PRIMARY KEY,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        declaration_type VARCHAR(30) NOT NULL,
        clauses         JSONB NOT NULL DEFAULT '[]',
        total_clauses   INTEGER NOT NULL DEFAULT 0,
        accepted_all    BOOLEAN NOT NULL DEFAULT FALSE,
        ip_address      VARCHAR(45),
        user_agent      VARCHAR(300),
        signed_at       TIMESTAMP NOT NULL DEFAULT NOW(),
        revoked_at      TIMESTAMP,
        created_at      TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_ethical_decl_user ON ethical_declarations(user_id, declaration_type);
    """)

    # ── 5. device_alerts + risk_level ─────────────
    op.execute("""
    DO $$ BEGIN
        ALTER TABLE device_alerts ADD COLUMN IF NOT EXISTS risk_level VARCHAR(5) DEFAULT 'R0';
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """)

    # ── 6. assessment_sessions + expires_at ───────
    op.execute("""
    DO $$ BEGIN
        ALTER TABLE assessment_sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """)


def downgrade():
    op.execute("ALTER TABLE assessment_sessions DROP COLUMN IF EXISTS expires_at")
    op.execute("ALTER TABLE device_alerts DROP COLUMN IF EXISTS risk_level")
    op.execute("DROP TABLE IF EXISTS ethical_declarations CASCADE")
    op.execute("DROP TABLE IF EXISTS user_contracts CASCADE")
    op.execute("DROP TABLE IF EXISTS ies_decision_log CASCADE")
    op.execute("DROP TABLE IF EXISTS ies_scores CASCADE")
