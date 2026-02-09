"""add content governance columns to knowledge_documents

Revision ID: 013
Revises: 012
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    # 证据分层
    op.add_column('knowledge_documents', sa.Column('evidence_tier', sa.String(2), server_default='T3', nullable=False))
    # 内容类型
    op.add_column('knowledge_documents', sa.Column('content_type', sa.String(30), nullable=True))
    # 原始材料发布日期
    op.add_column('knowledge_documents', sa.Column('published_date', sa.DateTime(), nullable=True))
    # 审核状态
    op.add_column('knowledge_documents', sa.Column('review_status', sa.String(20), nullable=True))
    # 审核人
    op.add_column('knowledge_documents', sa.Column('reviewer_id', sa.Integer(), nullable=True))
    # 审核时间
    op.add_column('knowledge_documents', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    # 贡献者
    op.add_column('knowledge_documents', sa.Column('contributor_id', sa.Integer(), nullable=True))
    # 过期时间
    op.add_column('knowledge_documents', sa.Column('expires_at', sa.DateTime(), nullable=True))

    # 索引
    op.create_index('idx_kdoc_review_status', 'knowledge_documents', ['review_status'])
    op.create_index('idx_kdoc_evidence_tier', 'knowledge_documents', ['evidence_tier'])
    op.create_index('idx_kdoc_contributor', 'knowledge_documents', ['contributor_id'])


def downgrade():
    op.drop_index('idx_kdoc_contributor', table_name='knowledge_documents')
    op.drop_index('idx_kdoc_evidence_tier', table_name='knowledge_documents')
    op.drop_index('idx_kdoc_review_status', table_name='knowledge_documents')

    op.drop_column('knowledge_documents', 'expires_at')
    op.drop_column('knowledge_documents', 'contributor_id')
    op.drop_column('knowledge_documents', 'reviewed_at')
    op.drop_column('knowledge_documents', 'reviewer_id')
    op.drop_column('knowledge_documents', 'review_status')
    op.drop_column('knowledge_documents', 'published_date')
    op.drop_column('knowledge_documents', 'content_type')
    op.drop_column('knowledge_documents', 'evidence_tier')
