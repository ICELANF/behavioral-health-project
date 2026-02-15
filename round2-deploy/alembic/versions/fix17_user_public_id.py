"""FIX-17: Add UUID public_id to users table

Revision ID: fix17_001
Revises: (set to current head)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "fix17_001"
down_revision = None  # ← 手动设置
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.add_column("users", sa.Column(
        "public_id", UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=True,
    ))
    op.execute("UPDATE users SET public_id = gen_random_uuid() WHERE public_id IS NULL")
    op.alter_column("users", "public_id", nullable=False)
    op.create_unique_constraint("uq_users_public_id", "users", ["public_id"])
    op.create_index("ix_users_public_id", "users", ["public_id"])


def downgrade():
    op.drop_index("ix_users_public_id")
    op.drop_constraint("uq_users_public_id", "users")
    op.drop_column("users", "public_id")
