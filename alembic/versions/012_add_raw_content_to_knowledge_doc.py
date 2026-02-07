"""add raw_content and updated_at to knowledge_documents

Revision ID: 012
Revises: 011
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('knowledge_documents', sa.Column('raw_content', sa.Text(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('knowledge_documents', 'updated_at')
    op.drop_column('knowledge_documents', 'raw_content')
