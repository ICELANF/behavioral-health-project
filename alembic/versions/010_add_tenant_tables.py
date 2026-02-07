"""add expert tenant tables

Revision ID: 010
Revises: 009
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # 专家租户表
    op.create_table(
        'expert_tenants',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('expert_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        # 品牌配置
        sa.Column('brand_name', sa.String(128), nullable=False),
        sa.Column('brand_tagline', sa.String(256), default=''),
        sa.Column('brand_avatar', sa.String(16), default='🏥'),
        sa.Column('brand_logo_url', sa.String(512), default=''),
        sa.Column('brand_colors', sa.JSON(), nullable=False),
        sa.Column('brand_theme_id', sa.String(32), default='default'),
        sa.Column('custom_domain', sa.String(256), default=''),
        # 专家人设
        sa.Column('expert_title', sa.String(64), default=''),
        sa.Column('expert_self_intro', sa.Text(), default=''),
        sa.Column('expert_specialties', sa.JSON(), nullable=True),
        sa.Column('expert_credentials', sa.JSON(), nullable=True),
        # Agent 配置
        sa.Column('enabled_agents', sa.JSON(), nullable=False),
        sa.Column('agent_persona_overrides', sa.JSON(), nullable=True),
        # 业务配置
        sa.Column('enabled_paths', sa.JSON(), nullable=True),
        sa.Column('service_packages', sa.JSON(), nullable=True),
        sa.Column('questionnaire_overrides', sa.JSON(), nullable=True),
        sa.Column('welcome_message', sa.Text(), default=''),
        # 控制
        sa.Column('status', sa.Enum('trial', 'active', 'suspended', 'archived', name='tenantstatus'), nullable=False, server_default='trial'),
        sa.Column('tier', sa.Enum('basic_partner', 'premium_partner', 'strategic_partner', name='tenanttier'), nullable=False, server_default='basic_partner'),
        sa.Column('max_clients', sa.Integer(), default=50),
        sa.Column('revenue_share_expert', sa.Float(), default=0.80),
        sa.Column('trial_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_tenant_status', 'expert_tenants', ['status'])
    op.create_index('idx_tenant_expert_user', 'expert_tenants', ['expert_user_id'])

    # 客户归属表
    op.create_table(
        'tenant_clients',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(64), sa.ForeignKey('expert_tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source', sa.String(32), default='expert_referred'),
        sa.Column('service_package', sa.String(64), default='trial'),
        sa.Column('status', sa.Enum('active', 'graduated', 'paused', 'exited', name='clientstatus'), nullable=False, server_default='active'),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('graduated_at', sa.DateTime(), nullable=True),
        sa.Column('total_sessions', sa.Integer(), default=0),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), default=''),
    )
    op.create_index('idx_tc_tenant_id', 'tenant_clients', ['tenant_id'])
    op.create_index('idx_tc_user_id', 'tenant_clients', ['user_id'])
    op.create_index('idx_tc_tenant_status', 'tenant_clients', ['tenant_id', 'status'])

    # Agent 映射表
    op.create_table(
        'tenant_agent_mappings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(64), sa.ForeignKey('expert_tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', sa.String(32), nullable=False),
        sa.Column('display_name', sa.String(64), default=''),
        sa.Column('display_avatar', sa.String(16), default=''),
        sa.Column('greeting', sa.Text(), default=''),
        sa.Column('tone', sa.String(128), default=''),
        sa.Column('bio', sa.String(256), default=''),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_tam_tenant_id', 'tenant_agent_mappings', ['tenant_id'])
    op.create_index('idx_tam_tenant_enabled', 'tenant_agent_mappings', ['tenant_id', 'is_enabled'])

    # 审计日志表
    op.create_table(
        'tenant_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(64), sa.ForeignKey('expert_tenants.id'), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('detail', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_audit_tenant_time', 'tenant_audit_logs', ['tenant_id', 'created_at'])


def downgrade():
    op.drop_table('tenant_audit_logs')
    op.drop_table('tenant_agent_mappings')
    op.drop_table('tenant_clients')
    op.drop_table('expert_tenants')
