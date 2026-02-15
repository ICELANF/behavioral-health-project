"""Security fixes: token hash comments + user public_id UUID

FIX-13: Mark token columns as hash storage
FIX-17: Add UUID public_id to users for external-facing IDs

Revision ID: 037
Revises: 036
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade():
    # ── FIX-13: Token hash storage ──
    # Enable pgcrypto for digest()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # Hash existing plaintext tokens (only those longer than 64 chars = not already hashed)
    op.execute("""
        UPDATE user_sessions
        SET token = encode(digest(token::bytea, 'sha256'), 'hex'),
            refresh_token = encode(digest(refresh_token::bytea, 'sha256'), 'hex')
        WHERE token IS NOT NULL
          AND length(token) > 64
    """)
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'SHA-256 hash of JWT token (FIX-13)'")
    op.execute("COMMENT ON COLUMN user_sessions.refresh_token IS 'SHA-256 hash of refresh token (FIX-13)'")

    # ── FIX-17: User public_id UUID ──
    op.add_column("users", sa.Column(
        "public_id",
        UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=True,
    ))
    op.execute("UPDATE users SET public_id = gen_random_uuid() WHERE public_id IS NULL")
    op.alter_column("users", "public_id", nullable=False)
    op.create_unique_constraint("uq_users_public_id", "users", ["public_id"])
    op.create_index("ix_users_public_id", "users", ["public_id"])


def downgrade():
    # FIX-17 rollback
    op.drop_index("ix_users_public_id")
    op.drop_constraint("uq_users_public_id", "users")
    op.drop_column("users", "public_id")
    # FIX-13: token hashes are irreversible
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'JWT token (was hashed in 036)'")
