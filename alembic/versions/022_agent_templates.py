"""add agent_templates table with 12 preset seeds

Revision ID: 022
Revises: 021
Create Date: 2026-02-12

Summary:
  V006 Agent 模板化 — agent_templates 表 + 12 个预置模板种子数据
"""
import json
import os
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_templates ──
    op.create_table(
        'agent_templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(64), nullable=False),
        sa.Column('agent_type', sa.String(20), server_default='specialist'),
        sa.Column('domain_enum', sa.String(32), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), server_default='[]'),
        sa.Column('data_fields', sa.JSON(), server_default='[]'),
        sa.Column('correlations', sa.JSON(), server_default='[]'),
        sa.Column('priority', sa.Integer(), server_default='5'),
        sa.Column('base_weight', sa.Float(), server_default='0.8'),
        sa.Column('enable_llm', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('conflict_wins_over', sa.JSON(), server_default='[]'),
        sa.Column('is_preset', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.text('true'), index=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # composite index
    op.create_index('idx_at_type_enabled', 'agent_templates', ['agent_type', 'is_enabled'])

    # ── seed 12 preset templates ──
    seed_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'configs', 'agent_templates_seed.json'
    )
    with open(seed_path, 'r', encoding='utf-8') as f:
        seeds = json.load(f)

    table = sa.table(
        'agent_templates',
        sa.column('agent_id', sa.String),
        sa.column('display_name', sa.String),
        sa.column('agent_type', sa.String),
        sa.column('domain_enum', sa.String),
        sa.column('description', sa.Text),
        sa.column('keywords', sa.JSON),
        sa.column('data_fields', sa.JSON),
        sa.column('correlations', sa.JSON),
        sa.column('priority', sa.Integer),
        sa.column('base_weight', sa.Float),
        sa.column('enable_llm', sa.Boolean),
        sa.column('system_prompt', sa.Text),
        sa.column('conflict_wins_over', sa.JSON),
        sa.column('is_preset', sa.Boolean),
        sa.column('is_enabled', sa.Boolean),
    )

    for seed in seeds:
        op.execute(
            table.insert().values(
                agent_id=seed['agent_id'],
                display_name=seed['display_name'],
                agent_type=seed['agent_type'],
                domain_enum=seed.get('domain_enum'),
                description=seed.get('description', ''),
                keywords=seed.get('keywords', []),
                data_fields=seed.get('data_fields', []),
                correlations=seed.get('correlations', []),
                priority=seed.get('priority', 5),
                base_weight=seed.get('base_weight', 0.8),
                enable_llm=seed.get('enable_llm', True),
                system_prompt=seed.get('system_prompt', ''),
                conflict_wins_over=seed.get('conflict_wins_over', []),
                is_preset=seed.get('is_preset', False),
                is_enabled=True,
            )
        )


def downgrade() -> None:
    op.drop_index('idx_at_type_enabled', table_name='agent_templates')
    op.drop_table('agent_templates')
