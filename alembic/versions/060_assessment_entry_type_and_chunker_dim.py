"""060 assessment_sessions.entry_type + chunker 768→1024 cleanup

- ADD COLUMN entry_type VARCHAR(20) DEFAULT 'self' to assessment_sessions
- chunker.py fallback dim 已在代码层从 768 切换至 1024 (无 DB 变更)

Revision ID: 060
Revises: 059
"""
revision = "060"
down_revision = "059"

from alembic import op


def upgrade():
    op.execute("""
        ALTER TABLE assessment_sessions
        ADD COLUMN IF NOT EXISTS entry_type VARCHAR(20) NOT NULL DEFAULT 'self'
    """)


def downgrade():
    op.execute("""
        ALTER TABLE assessment_sessions
        DROP COLUMN IF EXISTS entry_type
    """)
