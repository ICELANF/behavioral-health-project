"""add safety_logs and content_audio tables

Revision ID: 021
Revises: 020
Create Date: 2026-02-11

Summary:
  V005 多模态互动 — 安全日志表 + 内容音频附件表
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── safety_logs ──
    op.create_table(
        'safety_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('event_type', sa.String(30), nullable=False, index=True),
        sa.Column('severity', sa.String(15), nullable=False, server_default='low', index=True),
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('output_text', sa.Text(), nullable=True),
        sa.Column('filter_details', sa.JSON(), nullable=True),
        sa.Column('resolved', sa.Boolean(), server_default=sa.text('false'), index=True),
        sa.Column('resolved_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # ── content_audio ──
    op.create_table(
        'content_audio',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('content_item_id', sa.Integer(), sa.ForeignKey('content_items.id'), nullable=False, index=True),
        sa.Column('audio_url', sa.String(500), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('voice_type', sa.String(30), server_default='tts_female'),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('content_audio')
    op.drop_table('safety_logs')
