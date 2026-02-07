"""add knowledge base RAG tables

Revision ID: 011
Revises: 010
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # knowledge_documents
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('author', sa.String(100), nullable=True),
        sa.Column('source', sa.String(200), nullable=True),
        sa.Column('domain_id', sa.String(50), nullable=True),
        sa.Column('scope', sa.String(20), nullable=False, server_default='platform'),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='5'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('chunk_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_kdoc_scope_domain', 'knowledge_documents', ['scope', 'domain_id'])
    op.create_index('idx_kdoc_scope_tenant', 'knowledge_documents', ['scope', 'tenant_id'])
    op.create_index('idx_kdoc_status', 'knowledge_documents', ['status'])

    # knowledge_chunks
    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('heading', sa.String(200), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('chunk_index', sa.Integer(), server_default='0'),
        sa.Column('doc_title', sa.String(300), nullable=True),
        sa.Column('doc_author', sa.String(100), nullable=True),
        sa.Column('doc_source', sa.String(200), nullable=True),
        sa.Column('scope', sa.String(20), nullable=False, server_default='platform'),
        sa.Column('domain_id', sa.String(50), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_kchunk_doc', 'knowledge_chunks', ['document_id'])
    op.create_index('idx_kchunk_scope_domain', 'knowledge_chunks', ['scope', 'domain_id'])
    op.create_index('idx_kchunk_scope_tenant', 'knowledge_chunks', ['scope', 'tenant_id'])

    # knowledge_citations
    op.create_table(
        'knowledge_citations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('message_id', sa.String(100), nullable=True),
        sa.Column('agent_id', sa.String(50), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('user_id', sa.String(50), nullable=True),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.String(500), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('rank_position', sa.Integer(), nullable=True),
        sa.Column('citation_text', sa.String(500), nullable=True),
        sa.Column('citation_label', sa.String(300), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_kcite_session', 'knowledge_citations', ['session_id'])
    op.create_index('idx_kcite_doc', 'knowledge_citations', ['document_id'])
    op.create_index('idx_kcite_chunk', 'knowledge_citations', ['chunk_id'])


def downgrade():
    op.drop_table('knowledge_citations')
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
