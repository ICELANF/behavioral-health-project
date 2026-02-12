"""add routing config columns to tenant tables

Revision ID: 023
Revises: 022
Create Date: 2026-02-12

Summary:
  Phase 2 路由可配化 — ExpertTenant + TenantAgentMapping 新增路由配置列
  - ExpertTenant: routing_correlations, routing_conflicts, default_fallback_agent
  - TenantAgentMapping: custom_keywords, keyword_boost
"""
import sqlalchemy as sa
from alembic import op


revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- ExpertTenant: 路由级配置 --
    op.add_column('expert_tenants', sa.Column(
        'routing_correlations', sa.JSON(), server_default='{}',
        nullable=False, comment='专家自定义关联网络 {"sleep":["glucose","stress"]}'
    ))
    op.add_column('expert_tenants', sa.Column(
        'routing_conflicts', sa.JSON(), server_default='{}',
        nullable=False, comment='专家自定义冲突规则 {"sleep|exercise":"sleep"}'
    ))
    op.add_column('expert_tenants', sa.Column(
        'default_fallback_agent', sa.String(32), server_default='behavior_rx',
        nullable=False, comment='默认回退Agent'
    ))

    # -- TenantAgentMapping: 路由关键词 --
    op.add_column('tenant_agent_mappings', sa.Column(
        'custom_keywords', sa.JSON(), server_default='[]',
        nullable=False, comment='专家自定义路由关键词'
    ))
    op.add_column('tenant_agent_mappings', sa.Column(
        'keyword_boost', sa.Float(), server_default='1.5',
        nullable=False, comment='专家关键词得分加权倍数'
    ))


def downgrade() -> None:
    op.drop_column('tenant_agent_mappings', 'keyword_boost')
    op.drop_column('tenant_agent_mappings', 'custom_keywords')
    op.drop_column('expert_tenants', 'default_fallback_agent')
    op.drop_column('expert_tenants', 'routing_conflicts')
    op.drop_column('expert_tenants', 'routing_correlations')
