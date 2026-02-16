"""V4.1 Week3: 教练-学员绑定表 + 网关基础设施

Revision ID: v41_week3_001
Revises: v41_week2_001
Create Date: 2026-02-15

新增:
  1. coach_student_bindings 表 (coach_schema) — 权威绑定关系
  2. cross_layer_audit_log 表 (public) — 跨层访问审计
  3. 从现有数据回填绑定关系
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = 'v41_week3_001'
down_revision = 'v41_week2_001'  # ← 确认和你的实际revision一致
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ══════════════════════════════════════════
    # 1. 教练-学员绑定表 (coach_schema)
    # ══════════════════════════════════════════
    op.create_table(
        'coach_student_bindings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('coach_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('student_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('binding_type', sa.String(20), nullable=False, server_default='assigned',
                  comment='assigned|self_selected|program|challenge'),
        sa.Column('source_table', sa.String(50), comment='数据来源表'),
        sa.Column('source_id', UUID(as_uuid=True), comment='来源记录ID'),
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('permissions', JSONB, server_default='{"view_profile": true, "view_assessment_summary": true, "view_chat_summary": false, "send_message": true, "create_rx": true}',
                  comment='教练对该学员的权限'),
        sa.Column('bound_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('unbound_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('coach_id', 'student_id', 'binding_type', name='uq_coach_student_type'),
        schema='coach_schema',
    )

    # ══════════════════════════════════════════
    # 2. 跨层审计日志 (public)
    # ══════════════════════════════════════════
    op.create_table(
        'cross_layer_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('actor_id', UUID(as_uuid=True), nullable=False, index=True, comment='操作者ID'),
        sa.Column('actor_role', sa.String(20), nullable=False, comment='操作者角色'),
        sa.Column('target_user_id', UUID(as_uuid=True), nullable=True, index=True, comment='被访问的用户ID'),
        sa.Column('action', sa.String(50), nullable=False, comment='操作类型: view_profile|view_assessment|deliver_rx|send_message'),
        sa.Column('layer_from', sa.String(20), nullable=False, comment='来源层: professional|assistant|gateway'),
        sa.Column('layer_to', sa.String(20), nullable=False, comment='目标层'),
        sa.Column('resource_type', sa.String(50), comment='资源类型'),
        sa.Column('resource_id', sa.String(100), comment='资源ID'),
        sa.Column('sanitized_fields', JSONB, comment='被脱敏的字段列表'),
        sa.Column('result', sa.String(20), nullable=False, comment='allowed|denied|error'),
        sa.Column('denial_reason', sa.String(200), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        schema='public',
    )

    # ══════════════════════════════════════════
    # 3. 从现有数据回填绑定关系
    # ══════════════════════════════════════════
    op.execute("""
        -- 从 assessment_assignments 回填 (最可靠的来源)
        INSERT INTO coach_schema.coach_student_bindings
            (id, coach_id, student_id, binding_type, source_table, source_id, is_active, bound_at)
        SELECT
            gen_random_uuid(),
            coach_id,
            student_id,
            'assigned',
            'assessment_assignments',
            id,
            true,
            created_at
        FROM assessment_assignments
        WHERE coach_id IS NOT NULL AND student_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)

    op.execute("""
        -- 从 coach_messages 补充（可能有assignments没覆盖的绑定）
        INSERT INTO coach_schema.coach_student_bindings
            (id, coach_id, student_id, binding_type, source_table, is_active, bound_at)
        SELECT DISTINCT
            gen_random_uuid(),
            coach_id,
            student_id,
            'assigned',
            'coach_messages',
            true,
            MIN(created_at)
        FROM coach_schema.coach_messages
        WHERE coach_id IS NOT NULL AND student_id IS NOT NULL
        GROUP BY coach_id, student_id
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)

    op.execute("""
        -- 从 program_enrollments 补充
        INSERT INTO coach_schema.coach_student_bindings
            (id, coach_id, student_id, binding_type, source_table, source_id, is_active, bound_at)
        SELECT
            gen_random_uuid(),
            coach_id,
            user_id,
            'program',
            'program_enrollments',
            id,
            true,
            created_at
        FROM program_enrollments
        WHERE coach_id IS NOT NULL AND user_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)

    op.execute("""
        -- 从 challenge_enrollments 补充
        INSERT INTO coach_schema.coach_student_bindings
            (id, coach_id, student_id, binding_type, source_table, source_id, is_active, bound_at)
        SELECT
            gen_random_uuid(),
            coach_id,
            user_id,
            'challenge',
            'challenge_enrollments',
            id,
            true,
            created_at
        FROM challenge_enrollments
        WHERE coach_id IS NOT NULL AND user_id IS NOT NULL
        ON CONFLICT (coach_id, student_id, binding_type) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table('cross_layer_audit_log', schema='public')
    op.drop_table('coach_student_bindings', schema='coach_schema')
