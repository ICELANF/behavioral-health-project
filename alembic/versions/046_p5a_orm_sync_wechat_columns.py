"""P5A: ORM sync — WeChat columns already exist in physical DB (migration 044).
This migration verifies and adds only if missing (idempotent).

Revision ID: 046
Revises: 045
"""
from alembic import op
import sqlalchemy as sa

revision = "046"
down_revision = "045"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column exists in the physical database."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.first() is not None


def upgrade():
    # These columns were created by migration 044 (V5.0 flywheel).
    # This migration is ORM-sync only — add if somehow missing.
    cols = [
        ("wx_openid", sa.String(100)),
        ("union_id", sa.String(100)),
        ("wx_miniprogram_openid", sa.String(100)),
        ("preferred_channel", sa.String(20)),
        ("growth_points", sa.Integer()),
    ]
    for col_name, col_type in cols:
        if not _column_exists("users", col_name):
            op.add_column("users", sa.Column(col_name, col_type, nullable=True))

    # Ensure indexes exist
    try:
        op.create_index("ix_users_wx_openid", "users", ["wx_openid"], unique=True, if_not_exists=True)
    except Exception:
        pass
    try:
        op.create_index("ix_users_union_id", "users", ["union_id"], unique=True, if_not_exists=True)
    except Exception:
        pass


def downgrade():
    # Do not drop — these columns are used by the platform
    pass
