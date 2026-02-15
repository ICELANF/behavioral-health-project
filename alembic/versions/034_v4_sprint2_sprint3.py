"""V4.0 Sprint 2-3: reflection_journals + script_templates

Revision ID: 034
Revises: 033
Create Date: 2026-02-14
"""
from alembic import op
import sqlalchemy as sa

revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade():
    # ── reflection_journals ─────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS reflection_journals (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        title VARCHAR(200),
        content TEXT NOT NULL,
        journal_type VARCHAR(30) DEFAULT 'freeform',
        reflection_depth FLOAT DEFAULT 0.0,
        depth_level VARCHAR(20) DEFAULT 'surface',
        agency_mode_at_time VARCHAR(20),
        tags JSONB DEFAULT '[]'::jsonb,
        prompt_used VARCHAR(200),
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_rj_user ON reflection_journals(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rj_type ON reflection_journals(journal_type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rj_created ON reflection_journals(created_at);")

    # ── script_templates ────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS script_templates (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        domain VARCHAR(30) NOT NULL,
        stage VARCHAR(30) NOT NULL,
        scenario VARCHAR(50) NOT NULL,
        agency_mode VARCHAR(20) DEFAULT 'any',
        opening_line TEXT NOT NULL,
        key_questions JSONB DEFAULT '[]'::jsonb,
        response_templates JSONB DEFAULT '[]'::jsonb,
        closing_line TEXT,
        notes TEXT,
        tags JSONB DEFAULT '[]'::jsonb,
        difficulty VARCHAR(20) DEFAULT 'basic',
        evidence_source VARCHAR(200),
        is_active BOOLEAN DEFAULT true,
        usage_count INTEGER DEFAULT 0,
        created_by INTEGER,
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_st_domain ON script_templates(domain);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_st_stage ON script_templates(stage);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_st_scenario ON script_templates(scenario);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_st_active ON script_templates(is_active);")


def downgrade():
    op.execute("DROP TABLE IF EXISTS script_templates CASCADE;")
    op.execute("DROP TABLE IF EXISTS reflection_journals CASCADE;")
