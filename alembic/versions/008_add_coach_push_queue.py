"""add coach push queue

Revision ID: 008
Revises: 007
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'coach_push_queue',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('coach_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source_type', sa.String(30), nullable=False),
        sa.Column('source_id', sa.String(50), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_extra', sa.JSON(), nullable=True),
        sa.Column('suggested_time', sa.DateTime(), nullable=True),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.String(10), server_default='normal'),
        sa.Column('status', sa.String(10), nullable=False, server_default='pending'),
        sa.Column('coach_note', sa.String(500), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_cpq_coach_status', 'coach_push_queue', ['coach_id', 'status'])
    op.create_index('idx_cpq_student', 'coach_push_queue', ['student_id'])
    op.create_index('idx_cpq_source', 'coach_push_queue', ['source_type'])
    op.create_index('idx_cpq_scheduled', 'coach_push_queue', ['status', 'scheduled_time'])


def downgrade():
    op.drop_table('coach_push_queue')
