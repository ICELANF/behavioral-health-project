"""add challenge tables

Revision ID: 007
Revises: 006
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # challenge_templates
    op.create_table(
        'challenge_templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('cover_image', sa.String(500), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(100), nullable=True, unique=True),
        sa.Column('daily_push_times', sa.JSON(), nullable=True),
        sa.Column('day_topics', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('reviewer1_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewer1_status', sa.String(20), nullable=True),
        sa.Column('reviewer1_note', sa.Text(), nullable=True),
        sa.Column('reviewer1_at', sa.DateTime(), nullable=True),
        sa.Column('reviewer2_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewer2_status', sa.String(20), nullable=True),
        sa.Column('reviewer2_note', sa.Text(), nullable=True),
        sa.Column('reviewer2_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('enrollment_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_challenge_status', 'challenge_templates', ['status'])
    op.create_index('idx_challenge_category', 'challenge_templates', ['category'])
    op.create_index('idx_challenge_created_by', 'challenge_templates', ['created_by'])

    # challenge_day_pushes
    op.create_table(
        'challenge_day_pushes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('challenge_id', sa.Integer(), sa.ForeignKey('challenge_templates.id'), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('push_time', sa.String(20), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_core', sa.Boolean(), server_default='1'),
        sa.Column('tag', sa.String(20), server_default='core'),
        sa.Column('management_content', sa.Text(), nullable=True),
        sa.Column('behavior_guidance', sa.Text(), nullable=True),
        sa.Column('survey', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_cdp_challenge_day', 'challenge_day_pushes', ['challenge_id', 'day_number'])
    op.create_index('idx_cdp_day_time', 'challenge_day_pushes', ['day_number', 'push_time'])

    # challenge_enrollments
    op.create_table(
        'challenge_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('challenge_id', sa.Integer(), sa.ForeignKey('challenge_templates.id'), nullable=False),
        sa.Column('coach_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='enrolled'),
        sa.Column('current_day', sa.Integer(), server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_pushes', sa.Integer(), server_default='0'),
        sa.Column('completed_surveys', sa.Integer(), server_default='0'),
        sa.Column('streak_days', sa.Integer(), server_default='0'),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_ce_user_challenge', 'challenge_enrollments', ['user_id', 'challenge_id'])
    op.create_index('idx_ce_status', 'challenge_enrollments', ['status'])
    op.create_index('idx_ce_coach', 'challenge_enrollments', ['coach_id'])

    # challenge_survey_responses
    op.create_table(
        'challenge_survey_responses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('challenge_enrollments.id'), nullable=False),
        sa.Column('push_id', sa.Integer(), sa.ForeignKey('challenge_day_pushes.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('responses', sa.JSON(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_csr_enrollment', 'challenge_survey_responses', ['enrollment_id'])
    op.create_index('idx_csr_push', 'challenge_survey_responses', ['push_id'])
    op.create_index('idx_csr_user', 'challenge_survey_responses', ['user_id', 'submitted_at'])

    # challenge_push_logs
    op.create_table(
        'challenge_push_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('challenge_enrollments.id'), nullable=False),
        sa.Column('push_id', sa.Integer(), sa.ForeignKey('challenge_day_pushes.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_cpl_enrollment', 'challenge_push_logs', ['enrollment_id'])
    op.create_index('idx_cpl_push', 'challenge_push_logs', ['push_id'])
    op.create_index('idx_cpl_status', 'challenge_push_logs', ['status'])


def downgrade():
    op.drop_table('challenge_push_logs')
    op.drop_table('challenge_survey_responses')
    op.drop_table('challenge_enrollments')
    op.drop_table('challenge_day_pushes')
    op.drop_table('challenge_templates')
