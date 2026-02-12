"""Phase 3: 知识共享层 — knowledge_contributions 表 + scope 归一化

Revision ID: 024
Revises: 023
Create Date: 2026-02-12
"""

revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 1. 创建 knowledge_contributions 表
    op.create_table(
        'knowledge_contributions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.Integer(),
                   sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('contributor_id', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=False),
        sa.Column('domain_id', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewer_id', sa.Integer(),
                   sa.ForeignKey('users.id'), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('idx_kcontrib_status', 'knowledge_contributions', ['status'])
    op.create_index('idx_kcontrib_tenant', 'knowledge_contributions', ['tenant_id', 'status'])
    op.create_index('idx_kcontrib_domain', 'knowledge_contributions', ['domain_id', 'status'])

    # 2. 归一化 scope 值: 把 'global' 改为 'platform' (保持一致性)
    op.execute("""
        UPDATE knowledge_documents SET scope = 'platform' WHERE scope = 'global'
    """)
    op.execute("""
        UPDATE knowledge_chunks SET scope = 'platform' WHERE scope = 'global'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE knowledge_chunks SET scope = 'global' WHERE scope = 'platform'
    """)
    op.execute("""
        UPDATE knowledge_documents SET scope = 'global' WHERE scope = 'platform'
    """)
    op.drop_index('idx_kcontrib_domain', table_name='knowledge_contributions')
    op.drop_index('idx_kcontrib_tenant', table_name='knowledge_contributions')
    op.drop_index('idx_kcontrib_status', table_name='knowledge_contributions')
    op.drop_table('knowledge_contributions')
