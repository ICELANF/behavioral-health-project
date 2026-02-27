"""059_schema_sync_e2e

E2E 联调期间发现的 ORM vs DB 差异一次性同步。
- public.users: 5 cols (wx_openid, union_id, etc.)
- public.content_items: review_status
- public.expert_tenants: 7 cols
- public.responsibility_metrics: 4 cols  
- coach_schema.coach_push_queue: reviewer_id
- coach_schema.agent_templates: evidence_tier
- coach_schema.stage_transition_logs: table clone
- 18+ tables created via create_all (already exist)

Revision ID: 059
Revises: 058
"""
revision = "059"
down_revision = "058"

from alembic import op
import sqlalchemy as sa

def upgrade():
    # public.users
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wx_openid VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS union_id VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wx_miniprogram_openid VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_channel VARCHAR(32)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS growth_points INTEGER DEFAULT 0")

    # public.content_items
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS review_status VARCHAR(20)")

    # public.expert_tenants
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS credential_type VARCHAR(50)")
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS role_confirmed_by INTEGER")
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS role_confirmed_at TIMESTAMP")
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP")
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS suspension_count INTEGER DEFAULT 0")
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS workspace_ready BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE expert_tenants ADD COLUMN IF NOT EXISTS role_confirmed BOOLEAN DEFAULT false")

    # public.responsibility_metrics
    op.execute("ALTER TABLE responsibility_metrics ADD COLUMN IF NOT EXISTS checked_at TIMESTAMP")
    op.execute("ALTER TABLE responsibility_metrics ADD COLUMN IF NOT EXISTS value FLOAT")
    op.execute("ALTER TABLE responsibility_metrics ADD COLUMN IF NOT EXISTS detail JSON")
    op.execute("ALTER TABLE responsibility_metrics ADD COLUMN IF NOT EXISTS metric_type VARCHAR(50)")

    # coach_schema
    op.execute("ALTER TABLE coach_schema.coach_push_queue ADD COLUMN IF NOT EXISTS reviewer_id INTEGER")
    op.execute("ALTER TABLE coach_schema.agent_templates ADD COLUMN IF NOT EXISTS evidence_tier VARCHAR(20)")
    op.execute("CREATE TABLE IF NOT EXISTS coach_schema.stage_transition_logs (LIKE public.stage_transition_logs INCLUDING ALL)")

    # Missing tables created by ORM create_all during E2E:
    # observer_quota, agent_configs, agent_sessions, user_profiles,
    # assessment_results, assessment_profiles, supervisor_credentials,
    # role_change_logs, analytics_daily, feature_flags, ab_test_events,
    # prompt_templates, demo_requests (all IF NOT EXISTS via create_all)
    from core.models import Base
    from core import models
    bind = op.get_bind()
    Base.metadata.create_all(bind, checkfirst=True)

def downgrade():
    pass
