"""add exam, activity log, batch ingestion models

Revision ID: 016
Revises: 015
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    # exam_definitions
    op.create_table(
        'exam_definitions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('exam_id', sa.String(50), unique=True, nullable=False),
        sa.Column('exam_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('level', sa.String(10), nullable=True),
        sa.Column('exam_type', sa.String(30), server_default='standard'),
        sa.Column('passing_score', sa.Integer, server_default='60'),
        sa.Column('duration_minutes', sa.Integer, server_default='60'),
        sa.Column('max_attempts', sa.Integer, server_default='3'),
        sa.Column('question_ids', sa.JSON, nullable=True),
        sa.Column('status', sa.String(20), server_default='draft', nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_exam_status', 'exam_definitions', ['status'])
    op.create_index('idx_exam_level', 'exam_definitions', ['level'])

    # question_bank
    op.create_table(
        'question_bank',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('question_id', sa.String(50), unique=True, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),
        sa.Column('options', sa.JSON, nullable=True),
        sa.Column('answer', sa.JSON, nullable=False),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('domain', sa.String(50), nullable=True),
        sa.Column('difficulty', sa.String(20), server_default='medium'),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_qb_type', 'question_bank', ['question_type'])
    op.create_index('idx_qb_domain', 'question_bank', ['domain'])

    # exam_results
    op.create_table(
        'exam_results',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('exam_id', sa.String(50), nullable=False),
        sa.Column('attempt_number', sa.Integer, server_default='1'),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('answers', sa.JSON, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_er_user_exam', 'exam_results', ['user_id', 'exam_id'])
    op.create_index('idx_er_status', 'exam_results', ['status'])

    # user_activity_logs
    op.create_table(
        'user_activity_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('activity_type', sa.String(30), nullable=False),
        sa.Column('detail', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_ual_user_type', 'user_activity_logs', ['user_id', 'activity_type'])
    op.create_index('idx_ual_user_date', 'user_activity_logs', ['user_id', 'created_at'])

    # batch_ingestion_jobs
    op.create_table(
        'batch_ingestion_jobs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('filename', sa.String(300), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('total_files', sa.Integer, server_default='0'),
        sa.Column('processed_files', sa.Integer, server_default='0'),
        sa.Column('total_chunks', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('result_doc_ids', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_bij_status', 'batch_ingestion_jobs', ['status'])
    op.create_index('idx_bij_user', 'batch_ingestion_jobs', ['user_id'])


def downgrade():
    op.drop_table('batch_ingestion_jobs')
    op.drop_table('user_activity_logs')
    op.drop_table('exam_results')
    op.drop_table('question_bank')
    op.drop_table('exam_definitions')
