"""V007 Phase A: Policy Engine tables

Revision ID: 028
Revises: 027
Create Date: 2026-02-12

Creates 6 tables:
  policy_rules, rule_priority, agent_applicability_matrix,
  conflict_matrix, decision_trace, cost_budget_ledger
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade():
    # 1. policy_rules
    op.create_table(
        'policy_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('rule_name', sa.String(100), nullable=False, unique=True),
        sa.Column('rule_type', sa.String(30), nullable=False,
                  comment='routing|safety|cost|conflict|stage'),
        sa.Column('condition_expr', JSONB, nullable=False,
                  comment='JSON-Logic expression'),
        sa.Column('action_type', sa.String(30), nullable=False,
                  comment='select_agent|block|escalate|cost_limit'),
        sa.Column('action_params', JSONB, nullable=False),
        sa.Column('priority', sa.Integer(), server_default='50',
                  comment='0-100, higher = more priority'),
        sa.Column('tenant_id', sa.String(50), nullable=True,
                  comment='NULL=platform, value=tenant'),
        sa.Column('is_enabled', sa.Boolean(), server_default='true'),
        sa.Column('evidence_tier', sa.String(5), nullable=True,
                  comment='T1-T5'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )
    op.create_index('idx_policy_rules_type', 'policy_rules', ['rule_type', 'is_enabled'])
    op.create_index('idx_policy_rules_tenant', 'policy_rules', ['tenant_id', 'priority'])

    # 2. rule_priority
    op.create_table(
        'rule_priority',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('rule_id', sa.Integer(), sa.ForeignKey('policy_rules.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('parent_rule_id', sa.Integer(), sa.ForeignKey('policy_rules.id'),
                  nullable=True, comment='parent rule for priority tree'),
        sa.Column('level', sa.Integer(), server_default='0',
                  comment='depth: 0=root'),
        sa.Column('override_mode', sa.String(20), server_default='merge',
                  comment='merge|replace|append'),
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('effective_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_rule_priority_rule', 'rule_priority', ['rule_id'])

    # 3. agent_applicability_matrix
    op.create_table(
        'agent_applicability_matrix',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('stage_range', sa.String(20), nullable=False,
                  comment="'S0-S2' | 'S3-S6' | 'ALL'"),
        sa.Column('risk_level', sa.String(20), server_default='normal',
                  comment='low|normal|high|critical'),
        sa.Column('intensity_level', sa.Integer(), server_default='3',
                  comment='1-5'),
        sa.Column('max_daily_calls', sa.Integer(), server_default='10'),
        sa.Column('cooldown_hours', sa.Integer(), server_default='0'),
        sa.Column('contraindications', JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )
    op.create_index('idx_aam_agent', 'agent_applicability_matrix', ['agent_id', 'is_enabled'])
    op.create_index('idx_aam_stage', 'agent_applicability_matrix', ['stage_range', 'risk_level'])

    # 4. conflict_matrix
    op.create_table(
        'conflict_matrix',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_a_id', sa.String(50), nullable=False),
        sa.Column('agent_b_id', sa.String(50), nullable=False),
        sa.Column('conflict_type', sa.String(30), nullable=False,
                  comment='exclusive|cooperative|conditional'),
        sa.Column('resolution_strategy', sa.String(30), nullable=False,
                  comment='weighted_score|priority_tree|medical_boundary|tenant_override|risk_suppress'),
        sa.Column('winner_rule', JSONB, nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_conflict_agents', 'conflict_matrix', ['agent_a_id', 'agent_b_id'])

    # 5. decision_trace
    op.create_table(
        'decision_trace',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'),
                  primary_key=True),
        sa.Column('event_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('triggered_agents', JSONB, nullable=False),
        sa.Column('policy_applied', JSONB, nullable=False),
        sa.Column('rule_weights', JSONB, nullable=False),
        sa.Column('conflict_resolution', JSONB, nullable=True),
        sa.Column('final_output', sa.String(50), nullable=False),
        sa.Column('secondary_agents', JSONB, nullable=True),
        sa.Column('llm_model', sa.String(50), nullable=True),
        sa.Column('token_cost', sa.Integer(), server_default='0'),
        sa.Column('latency_ms', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_trace_user', 'decision_trace',
                    ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_trace_tenant', 'decision_trace',
                    ['tenant_id', sa.text('created_at DESC')])
    op.create_index('idx_trace_event', 'decision_trace', ['event_id'])

    # 6. cost_budget_ledger
    op.create_table(
        'cost_budget_ledger',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('budget_type', sa.String(20), nullable=False,
                  comment='daily|monthly|total'),
        sa.Column('max_tokens', sa.BigInteger(), nullable=False),
        sa.Column('used_tokens', sa.BigInteger(), server_default='0'),
        sa.Column('max_cost_cny', sa.Numeric(10, 4), nullable=True),
        sa.Column('used_cost_cny', sa.Numeric(10, 4), server_default='0'),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('overflow_action', sa.String(20), server_default='downgrade',
                  comment='downgrade|queue|block'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )
    op.create_index('idx_budget_tenant', 'cost_budget_ledger',
                    ['tenant_id', 'budget_type', 'is_active'])


def downgrade():
    op.drop_table('cost_budget_ledger')
    op.drop_table('decision_trace')
    op.drop_table('conflict_matrix')
    op.drop_table('agent_applicability_matrix')
    op.drop_table('rule_priority')
    op.drop_table('policy_rules')
