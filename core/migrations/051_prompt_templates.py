"""
Migration 051: Prompt 模板表

前端 admin-portal/src/views/admin/prompts/ 已就绪，后端缺少表和 API。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine


def upgrade():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id              SERIAL PRIMARY KEY,
                name            VARCHAR(100) NOT NULL,
                description     VARCHAR(500),
                category        VARCHAR(30) NOT NULL,
                content         TEXT NOT NULL,
                variables       JSONB DEFAULT '[]'::jsonb,
                ttm_stage       VARCHAR(30),
                trigger_domain  VARCHAR(30),
                is_active       BOOLEAN NOT NULL DEFAULT TRUE,
                created_by      INTEGER REFERENCES users(id),
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS idx_pt_category ON prompt_templates(category);
            CREATE INDEX IF NOT EXISTS idx_pt_ttm_stage ON prompt_templates(ttm_stage);
            CREATE INDEX IF NOT EXISTS idx_pt_trigger_domain ON prompt_templates(trigger_domain);
            CREATE INDEX IF NOT EXISTS idx_pt_is_active ON prompt_templates(is_active);
        """))
    print("[Migration 051] prompt_templates table created")


def downgrade():
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS prompt_templates;"))
    print("[Migration 051] prompt_templates table dropped")


if __name__ == "__main__":
    upgrade()
