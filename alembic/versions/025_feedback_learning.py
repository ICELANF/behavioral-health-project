"""Phase 4: 反馈学习闭环 — agent_feedbacks + agent_metrics_daily + agent_prompt_versions

Revision ID: 025
Revises: 024
Create Date: 2026-02-12
"""

revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 1. agent_feedbacks — 持久化反馈记录
    op.create_table(
        'agent_feedbacks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(32), nullable=False),
        sa.Column('user_id', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('feedback_type', sa.String(20), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('modifications', sa.JSON(), nullable=True),
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('agent_response', sa.Text(), nullable=True),
        sa.Column('agents_used', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_af_agent_time', 'agent_feedbacks', ['agent_id', 'created_at'])
    op.create_index('idx_af_user', 'agent_feedbacks', ['user_id', 'created_at'])
    op.create_index('idx_af_tenant', 'agent_feedbacks', ['tenant_id'])

    # 2. agent_metrics_daily — 日维度聚合指标
    op.create_table(
        'agent_metrics_daily',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(32), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('total_calls', sa.Integer(), server_default='0'),
        sa.Column('llm_calls', sa.Integer(), server_default='0'),
        sa.Column('feedback_count', sa.Integer(), server_default='0'),
        sa.Column('accept_count', sa.Integer(), server_default='0'),
        sa.Column('reject_count', sa.Integer(), server_default='0'),
        sa.Column('modify_count', sa.Integer(), server_default='0'),
        sa.Column('rate_count', sa.Integer(), server_default='0'),
        sa.Column('total_rating', sa.Integer(), server_default='0'),
        sa.Column('avg_processing_ms', sa.Float(), server_default='0'),
        sa.Column('avg_confidence', sa.Float(), server_default='0'),
        sa.Column('acceptance_rate', sa.Float(), server_default='0'),
        sa.Column('avg_rating', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_amd_agent_date', 'agent_metrics_daily',
                     ['agent_id', 'metric_date'], unique=True)

    # 3. agent_prompt_versions — prompt 版本追踪
    op.create_table(
        'agent_prompt_versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(32), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('traffic_pct', sa.Integer(), server_default='100'),
        sa.Column('prev_avg_rating', sa.Float(), nullable=True),
        sa.Column('prev_acceptance_rate', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_apv_agent_version', 'agent_prompt_versions',
                     ['agent_id', 'version'], unique=True)
    op.create_index('idx_apv_agent_active', 'agent_prompt_versions', ['agent_id'])

    # 4. 为现有 12 个 Agent 模板创建 v1 prompt 版本记录
    op.execute("""
        INSERT INTO agent_prompt_versions (agent_id, version, system_prompt, is_active, traffic_pct, change_reason)
        SELECT agent_id, 1, COALESCE(system_prompt, ''), true, 100, 'initial seed from agent_templates'
        FROM agent_templates
        WHERE system_prompt IS NOT NULL AND system_prompt != ''
    """)


def downgrade() -> None:
    op.drop_index('idx_apv_agent_active', table_name='agent_prompt_versions')
    op.drop_index('idx_apv_agent_version', table_name='agent_prompt_versions')
    op.drop_table('agent_prompt_versions')
    op.drop_index('idx_amd_agent_date', table_name='agent_metrics_daily')
    op.drop_table('agent_metrics_daily')
    op.drop_index('idx_af_tenant', table_name='agent_feedbacks')
    op.drop_index('idx_af_user', table_name='agent_feedbacks')
    op.drop_index('idx_af_agent_time', table_name='agent_feedbacks')
    op.drop_table('agent_feedbacks')
