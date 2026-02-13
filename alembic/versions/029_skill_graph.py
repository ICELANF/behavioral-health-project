"""V007 Phase B: Skill Graph + Effectiveness tables

Revision ID: 029
Revises: 028
Create Date: 2026-02-12

Creates 9 tables:
  expert_domain, intervention_protocol, risk_boundary,
  stage_applicability, contraindications, evidence_tier_binding,
  agent_skill_graph, policy_intervention_outcome, policy_stage_transition_log
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade():
    # 1. expert_domain
    op.create_table(
        'expert_domain',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('domain_name', sa.String(100), nullable=False),
        sa.Column('domain_type', sa.String(30), nullable=False,
                  comment='primary|secondary|supportive'),
        sa.Column('knowledge_scope', JSONB, nullable=True),
        sa.Column('authority_level', sa.Integer(), server_default='3',
                  comment='1-5'),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_expert_domain_agent', 'expert_domain', ['agent_id'])

    # 2. intervention_protocol
    op.create_table(
        'intervention_protocol',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('protocol_name', sa.String(100), nullable=False),
        sa.Column('trigger_condition', JSONB, nullable=False),
        sa.Column('response_template', sa.Text(), nullable=True),
        sa.Column('intensity_range', sa.String(10), server_default='1-5'),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('success_criteria', JSONB, nullable=True),
        sa.Column('escalation_protocol', sa.String(100), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_intv_protocol_agent', 'intervention_protocol', ['agent_id'])

    # 3. risk_boundary
    op.create_table(
        'risk_boundary',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('risk_type', sa.String(50), nullable=False,
                  comment='medical_emergency|psychological_crisis|data_anomaly'),
        sa.Column('max_risk_level', sa.String(20), nullable=False),
        sa.Column('escalation_target', sa.String(50), nullable=False),
        sa.Column('auto_exit_condition', JSONB, nullable=True),
        sa.Column('alert_message', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_risk_boundary_agent', 'risk_boundary', ['agent_id'])

    # 4. stage_applicability
    op.create_table(
        'stage_applicability',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('stage_code', sa.String(5), nullable=False,
                  comment='S0|S1|S2|S3|S4|S5|S6'),
        sa.Column('effectiveness_score', sa.Float(), server_default='0.5'),
        sa.Column('recommended_intensity', sa.Integer(), server_default='3'),
        sa.Column('is_primary', sa.Boolean(), server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_stage_app_agent', 'stage_applicability',
                    ['agent_id', 'stage_code'])
    op.create_index('idx_stage_app_primary', 'stage_applicability',
                    ['stage_code', 'is_primary'])

    # 5. contraindications
    op.create_table(
        'contraindications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('condition_type', sa.String(30), nullable=False,
                  comment='medical|psychological|behavioral|stage'),
        sa.Column('condition_value', sa.String(200), nullable=False),
        sa.Column('severity', sa.String(20), server_default='warning',
                  comment='warning|block'),
        sa.Column('alternative_agent_id', sa.String(50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_contra_agent', 'contraindications', ['agent_id'])

    # 6. evidence_tier_binding
    op.create_table(
        'evidence_tier_binding',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('evidence_tier', sa.String(5), nullable=False,
                  comment='T1-T5'),
        sa.Column('source_documents', JSONB, nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewer', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_evidence_agent', 'evidence_tier_binding', ['agent_id'])

    # 7. agent_skill_graph
    op.create_table(
        'agent_skill_graph',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False, unique=True),
        sa.Column('skill_vector', JSONB, nullable=False,
                  comment='9-dim capability vector'),
        sa.Column('capability_fingerprint', sa.String(64), nullable=True),
        sa.Column('last_calibrated_at', sa.DateTime(), nullable=True),
        sa.Column('calibration_source', sa.String(50), nullable=True,
                  comment='manual|auto|hybrid'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )

    # 8. policy_intervention_outcome (V007 version, distinct from m019 intervention_outcomes)
    op.create_table(
        'policy_intervention_outcome',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('intervention_start', sa.DateTime(), nullable=False),
        sa.Column('intervention_end', sa.DateTime(), nullable=True),
        sa.Column('ies_score', sa.Float(), nullable=True,
                  comment='Intervention Effectiveness Score'),
        sa.Column('stage_before', sa.String(5), nullable=True),
        sa.Column('stage_after', sa.String(5), nullable=True),
        sa.Column('adherence_index', sa.Float(), nullable=True),
        sa.Column('risk_delta', sa.Float(), nullable=True),
        sa.Column('token_cost_total', sa.Integer(), server_default='0'),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_policy_outcome_user', 'policy_intervention_outcome',
                    ['user_id', 'agent_id'])

    # 9. policy_stage_transition_log (V007 version, distinct from m019 stage_transition_logs)
    op.create_table(
        'policy_stage_transition_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('from_stage', sa.String(5), nullable=False),
        sa.Column('to_stage', sa.String(5), nullable=False),
        sa.Column('trigger_agent_id', sa.String(50), nullable=True),
        sa.Column('trigger_event', sa.String(100), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.8'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_policy_stage_trans_user', 'policy_stage_transition_log',
                    ['user_id', 'created_at'])


def downgrade():
    op.drop_table('policy_stage_transition_log')
    op.drop_table('policy_intervention_outcome')
    op.drop_table('agent_skill_graph')
    op.drop_table('evidence_tier_binding')
    op.drop_table('contraindications')
    op.drop_table('stage_applicability')
    op.drop_table('risk_boundary')
    op.drop_table('intervention_protocol')
    op.drop_table('expert_domain')
