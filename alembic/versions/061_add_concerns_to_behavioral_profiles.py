"""061 add concerns + voice_emotions to behavioral_profiles

Store user fill-in-the-blank concerns (worry/confusion/desire/aversion)
and voice emotion analysis results in the behavioral profile.

Revision ID: 061
Revises: 060
"""
revision = "061"
down_revision = "060"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("behavioral_profiles", sa.Column("concerns", sa.JSON, nullable=True,
        comment='{"worry":"...", "confusion":"...", "desire":"...", "aversion":"..."}'))
    op.add_column("behavioral_profiles", sa.Column("voice_emotions", sa.JSON, nullable=True,
        comment='{"worry":"anxious", "desire":"hopeful", ...}'))


def downgrade():
    op.drop_column("behavioral_profiles", "voice_emotions")
    op.drop_column("behavioral_profiles", "concerns")
