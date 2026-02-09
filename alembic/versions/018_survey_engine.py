"""018: 通用问卷引擎 5张表

- surveys (问卷主表)
- survey_questions (题目表)
- survey_responses (回收表)
- survey_response_answers (逐题答案)
- survey_distributions (分发渠道)

Revision ID: 018
Revises: 017
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    # 1. surveys 问卷主表
    op.create_table('surveys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), default=''),
        sa.Column('survey_type', sa.Enum('general', 'health', 'satisfaction', 'screening', 'feedback', 'registration', name='surveytype'), default='general'),
        sa.Column('status', sa.Enum('draft', 'published', 'closed', 'archived', name='surveystatus'), default='draft'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', sa.String(64), sa.ForeignKey('expert_tenants.id'), nullable=True),
        sa.Column('settings', sa.JSON(), default={}),
        sa.Column('baps_mapping', sa.JSON(), nullable=True),
        sa.Column('response_count', sa.Integer(), default=0),
        sa.Column('avg_duration', sa.Integer(), default=0),
        sa.Column('short_code', sa.String(8), unique=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_surveys_status', 'surveys', ['status'])
    op.create_index('idx_surveys_created_by', 'surveys', ['created_by'])
    op.create_index('idx_surveys_tenant', 'surveys', ['tenant_id'])

    # 2. survey_questions 题目表
    op.create_table('survey_questions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_type', sa.Enum(
            'single_choice', 'multiple_choice', 'text_short', 'text_long',
            'rating', 'nps', 'slider', 'matrix_single', 'matrix_multiple',
            'date', 'file_upload', 'section_break', 'description',
            name='questiontype'), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), default=''),
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('config', sa.JSON(), default={}),
        sa.Column('skip_logic', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_sq_survey', 'survey_questions', ['survey_id', 'sort_order'])

    # 3. survey_responses 回收表
    op.create_table('survey_responses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('respondent_ip', sa.String(45), nullable=True),
        sa.Column('respondent_ua', sa.String(500), nullable=True),
        sa.Column('device_type', sa.String(20), default='unknown'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.Column('is_complete', sa.Boolean(), default=False),
        sa.Column('current_page', sa.Integer(), default=0),
        sa.Column('baps_synced', sa.Boolean(), default=False),
        sa.Column('baps_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_sr_survey', 'survey_responses', ['survey_id'])
    op.create_index('idx_sr_user', 'survey_responses', ['user_id'])
    op.create_index('idx_sr_complete', 'survey_responses', ['survey_id', 'is_complete'])

    # 4. survey_response_answers 逐题答案
    op.create_table('survey_response_answers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('response_id', sa.Integer(), sa.ForeignKey('survey_responses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('survey_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answer_value', sa.JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_sra_response', 'survey_response_answers', ['response_id'])
    op.create_index('idx_sra_question', 'survey_response_answers', ['question_id'])
    op.create_index('idx_sra_unique', 'survey_response_answers', ['response_id', 'question_id'], unique=True)

    # 5. survey_distributions 分发渠道
    op.create_table('survey_distributions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.Enum('link', 'qrcode', 'wechat', 'sms', 'email', 'embed', 'coach', name='distributionchannel'), nullable=False),
        sa.Column('channel_config', sa.JSON(), default={}),
        sa.Column('tracking_code', sa.String(20), unique=True),
        sa.Column('click_count', sa.Integer(), default=0),
        sa.Column('submit_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )


def downgrade():
    op.drop_table('survey_distributions')
    op.drop_table('survey_response_answers')
    op.drop_table('survey_responses')
    op.drop_table('survey_questions')
    op.drop_table('surveys')
    op.execute("DROP TYPE IF EXISTS surveytype")
    op.execute("DROP TYPE IF EXISTS surveystatus")
    op.execute("DROP TYPE IF EXISTS questiontype")
    op.execute("DROP TYPE IF EXISTS distributionchannel")
