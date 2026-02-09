"""add learning persistence models (learning_progress, learning_time_logs, learning_points_logs, user_learning_stats)

Revision ID: 015
Revises: 014
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    # learning_progress
    op.create_table(
        'learning_progress',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_id', sa.Integer, sa.ForeignKey('content_items.id'), nullable=False),
        sa.Column('progress_percent', sa.Float, server_default='0'),
        sa.Column('last_position', sa.String(50), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer, server_default='0'),
        sa.Column('status', sa.String(20), server_default='not_started'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_lp_user_content', 'learning_progress', ['user_id', 'content_id'], unique=True)
    op.create_index('idx_lp_status', 'learning_progress', ['status'])

    # learning_time_logs
    op.create_table(
        'learning_time_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_id', sa.Integer, nullable=True),
        sa.Column('domain', sa.String(50), nullable=True),
        sa.Column('minutes', sa.Integer, nullable=False),
        sa.Column('earned_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_ltl_user_date', 'learning_time_logs', ['user_id', 'earned_at'])

    # learning_points_logs
    op.create_table(
        'learning_points_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(50), nullable=True),
        sa.Column('points', sa.Integer, nullable=False),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('earned_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_lpl_user_cat', 'learning_points_logs', ['user_id', 'category'])
    op.create_index('idx_lpl_user_date', 'learning_points_logs', ['user_id', 'earned_at'])

    # user_learning_stats
    op.create_table(
        'user_learning_stats',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('total_minutes', sa.Integer, server_default='0'),
        sa.Column('total_points', sa.Integer, server_default='0'),
        sa.Column('growth_points', sa.Integer, server_default='0'),
        sa.Column('contribution_points', sa.Integer, server_default='0'),
        sa.Column('influence_points', sa.Integer, server_default='0'),
        sa.Column('current_streak', sa.Integer, server_default='0'),
        sa.Column('longest_streak', sa.Integer, server_default='0'),
        sa.Column('last_learn_date', sa.String(10), nullable=True),
        sa.Column('quiz_total', sa.Integer, server_default='0'),
        sa.Column('quiz_passed', sa.Integer, server_default='0'),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_uls_points', 'user_learning_stats', ['total_points'])


def downgrade():
    op.drop_table('user_learning_stats')
    op.drop_table('learning_points_logs')
    op.drop_table('learning_time_logs')
    op.drop_table('learning_progress')
