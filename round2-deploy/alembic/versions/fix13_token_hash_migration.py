"""FIX-13: Hash existing plaintext tokens in user_sessions

Revision ID: fix13_001
Revises: (set to current head)
"""
from alembic import op

revision = "fix13_001"
down_revision = None  # ← 手动设置为当前 alembic head
branch_labels = None
depends_on = None


def upgrade():
    # 将现有明文 token 替换为 SHA-256 哈希
    # PostgreSQL digest() 需要 pgcrypto 扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("""
        UPDATE user_sessions
        SET token = encode(digest(token, 'sha256'), 'hex'),
            refresh_token = encode(digest(refresh_token, 'sha256'), 'hex')
        WHERE token IS NOT NULL
          AND length(token) > 64
    """)
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'SHA-256 hash (FIX-13)'")
    op.execute("COMMENT ON COLUMN user_sessions.refresh_token IS 'SHA-256 hash (FIX-13)'")


def downgrade():
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'Hashed in FIX-13, cannot revert'")
