"""V4.1 Week3: coach_student_bindings + cross_layer_audit_log

Revision ID: 039
Revises: 038
Create Date: 2026-02-15

New tables:
  1. coach_schema.coach_student_bindings — authoritative coach-student bindings
  2. public.cross_layer_audit_log — cross-layer access audit
  3. Backfill bindings from existing data
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '039'
down_revision = '038'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ══════════════════════════════════════════
    # 1. coach_student_bindings (coach_schema)
    # ══════════════════════════════════════════
    op.create_table(
        'coach_student_bindings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('coach_id', sa.Integer, nullable=False, index=True),
        sa.Column('student_id', sa.Integer, nullable=False, index=True),
        sa.Column('binding_type', sa.String(20), nullable=False,
                  server_default='assigned',
                  comment='assigned|self_selected|program|challenge'),
        sa.Column('source_table', sa.String(50), comment='backfill source'),
        sa.Column('source_id', sa.String(100), comment='source record ID'),
        sa.Column('is_active', sa.Boolean, server_default='true',
                  nullable=False),
        sa.Column('permissions', JSONB,
                  server_default='{"view_profile": true, "view_assessment_summary": true, "view_chat_summary": false, "send_message": true, "create_rx": true}',
                  comment='per-binding permissions'),
        sa.Column('bound_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('unbound_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.UniqueConstraint('coach_id', 'student_id', 'binding_type',
                            name='uq_coach_student_type'),
        schema='coach_schema',
    )

    # ══════════════════════════════════════════
    # 2. cross_layer_audit_log (public)
    # ══════════════════════════════════════════
    op.create_table(
        'cross_layer_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('timestamp', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), index=True),
        sa.Column('actor_id', sa.Integer, nullable=False, index=True,
                  comment='actor user ID'),
        sa.Column('actor_role', sa.String(20), nullable=False),
        sa.Column('target_user_id', sa.Integer, nullable=True, index=True),
        sa.Column('action', sa.String(50), nullable=False,
                  comment='view_profile|view_assessment|deliver_rx|etc'),
        sa.Column('layer_from', sa.String(20), nullable=False),
        sa.Column('layer_to', sa.String(20), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(100)),
        sa.Column('sanitized_fields', JSONB),
        sa.Column('result', sa.String(20), nullable=False,
                  comment='allowed|denied|error'),
        sa.Column('denial_reason', sa.String(200), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        schema='public',
    )

    # ══════════════════════════════════════════
    # 3. Backfill from existing data
    # ══════════════════════════════════════════

    # assessment_assignments (most reliable)
    op.execute("""
        INSERT INTO coach_schema.coach_student_bindings
            (coach_id, student_id, binding_type, source_table,
             source_id, is_active, bound_at)
        SELECT
            coach_id, student_id, 'assigned',
            'assessment_assignments', CAST(id AS TEXT),
            true, created_at
        FROM assessment_assignments
        WHERE coach_id IS NOT NULL AND student_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)

    # coach_messages (supplement)
    op.execute("""
        INSERT INTO coach_schema.coach_student_bindings
            (coach_id, student_id, binding_type, source_table,
             is_active, bound_at)
        SELECT DISTINCT ON (coach_id, student_id)
            coach_id, student_id, 'assigned',
            'coach_messages', true, MIN(created_at) OVER (PARTITION BY coach_id, student_id)
        FROM coach_schema.coach_messages
        WHERE coach_id IS NOT NULL AND student_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)

    # program_enrollments
    op.execute("""
        INSERT INTO coach_schema.coach_student_bindings
            (coach_id, student_id, binding_type, source_table,
             source_id, is_active, bound_at)
        SELECT
            CAST(coach_id AS INTEGER), CAST(user_id AS INTEGER), 'program',
            'program_enrollments', CAST(id AS TEXT),
            true, created_at
        FROM program_enrollments
        WHERE coach_id IS NOT NULL AND user_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)

    # challenge_enrollments (uses enrolled_at, not created_at)
    op.execute("""
        INSERT INTO coach_schema.coach_student_bindings
            (coach_id, student_id, binding_type, source_table,
             source_id, is_active, bound_at)
        SELECT
            CAST(coach_id AS INTEGER), CAST(user_id AS INTEGER), 'challenge',
            'challenge_enrollments', CAST(id AS TEXT),
            true, enrolled_at
        FROM challenge_enrollments
        WHERE coach_id IS NOT NULL AND user_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table('cross_layer_audit_log', schema='public')
    op.drop_table('coach_student_bindings', schema='coach_schema')
