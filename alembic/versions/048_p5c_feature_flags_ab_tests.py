"""P5C: feature_flags + ab_test_events tables.

Revision ID: 048
Revises: 047
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "048"
down_revision = "047"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="false"),
        sa.Column("rollout_pct", sa.Integer(), server_default="0"),
        sa.Column("variants", JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("targeting_rules", JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "ab_test_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("experiment_key", sa.String(100), nullable=False),
        sa.Column("variant", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_data", JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_ab_test_events_user", "ab_test_events", ["user_id"])
    op.create_index("ix_ab_test_events_exp", "ab_test_events", ["experiment_key"])

    # Pre-seed default feature flags
    op.execute("""
        INSERT INTO feature_flags (key, description, enabled, rollout_pct, variants)
        VALUES
          ('observer_home_variant', 'Observer首页A/B测试', true, 50, '["control","variant_a"]'),
          ('onboarding_flow', '引导流程开关', true, 100, '["control","guided"]'),
          ('push_frequency', '推送频率A/B测试', false, 30, '["control","high_freq","low_freq"]')
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade():
    op.drop_table("ab_test_events")
    op.drop_table("feature_flags")
