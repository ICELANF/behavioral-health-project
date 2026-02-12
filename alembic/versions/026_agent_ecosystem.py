"""Phase 5: Agent 生态 — marketplace + compositions + growth_points

Revision ID: 026
Revises: 025
Create Date: 2026-02-12
"""

revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 1. agent_marketplace_listings — 模板市场
    op.create_table(
        'agent_marketplace_listings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('template_id', sa.Integer(),
                   sa.ForeignKey('agent_templates.id'), nullable=False),
        sa.Column('publisher_id', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('title', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('tags', sa.JSON(), server_default='[]'),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('reviewer_id', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('install_count', sa.Integer(), server_default='0'),
        sa.Column('avg_rating', sa.Float(), server_default='0'),
        sa.Column('rating_count', sa.Integer(), server_default='0'),
        sa.Column('version', sa.String(20), server_default='1.0.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_aml_status', 'agent_marketplace_listings', ['status'])
    op.create_index('idx_aml_category', 'agent_marketplace_listings', ['category', 'status'])
    op.create_index('idx_aml_publisher', 'agent_marketplace_listings', ['publisher_id'])

    # 2. agent_compositions — 组合编排
    op.create_table(
        'agent_compositions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('created_by', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=False),
        sa.Column('pipeline', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('merge_strategy', sa.String(30), server_default='weighted_average'),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_ac_tenant', 'agent_compositions', ['tenant_id', 'is_enabled'])

    # 3. agent_growth_points — 成长积分
    op.create_table(
        'agent_growth_points',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=False),
        sa.Column('agent_id', sa.String(32), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_agp_user', 'agent_growth_points', ['user_id', 'created_at'])
    op.create_index('idx_agp_event', 'agent_growth_points', ['event_type'])


def downgrade() -> None:
    op.drop_index('idx_agp_event', table_name='agent_growth_points')
    op.drop_index('idx_agp_user', table_name='agent_growth_points')
    op.drop_table('agent_growth_points')
    op.drop_index('idx_ac_tenant', table_name='agent_compositions')
    op.drop_table('agent_compositions')
    op.drop_index('idx_aml_publisher', table_name='agent_marketplace_listings')
    op.drop_index('idx_aml_category', table_name='agent_marketplace_listings')
    op.drop_index('idx_aml_status', table_name='agent_marketplace_listings')
    op.drop_table('agent_marketplace_listings')
