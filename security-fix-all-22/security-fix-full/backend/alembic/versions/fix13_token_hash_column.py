"""FIX-13: Rename token columns to indicate hash storage

Revision ID: fix13_001
"""
from alembic import op
import sqlalchemy as sa

revision = "fix13_001"
down_revision = None  # 手动设置为当前最新 revision
branch_labels = None
depends_on = None


def upgrade():
    # 添加注释标记为 hash, 不改列名 (避免破坏现有代码)
    # 数据迁移: 将现有明文 token 替换为哈希
    op.execute("""
        UPDATE user_sessions
        SET token = encode(digest(token, 'sha256'), 'hex'),
            refresh_token = encode(digest(refresh_token, 'sha256'), 'hex')
        WHERE token IS NOT NULL
          AND length(token) > 64
    """)

    # 添加注释
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'SHA-256 hash of JWT token'")
    op.execute("COMMENT ON COLUMN user_sessions.refresh_token IS 'SHA-256 hash of refresh token'")


def downgrade():
    # 不可逆: 哈希无法还原为明文
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'JWT token (was hashed in fix13)'")
