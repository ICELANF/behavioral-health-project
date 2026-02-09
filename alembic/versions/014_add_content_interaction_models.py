"""add content interaction models (content_items, content_likes, content_bookmarks, content_comments)

Revision ID: 014
Revises: 013
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    # content_items
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('content_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('body', sa.Text, nullable=True),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('media_url', sa.String(500), nullable=True),
        sa.Column('domain', sa.String(50), nullable=True),
        sa.Column('level', sa.String(10), nullable=True),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft', nullable=False),
        sa.Column('view_count', sa.Integer, server_default='0'),
        sa.Column('like_count', sa.Integer, server_default='0'),
        sa.Column('comment_count', sa.Integer, server_default='0'),
        sa.Column('collect_count', sa.Integer, server_default='0'),
        sa.Column('has_quiz', sa.Boolean, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_ci_type_status', 'content_items', ['content_type', 'status'])
    op.create_index('idx_ci_domain_level', 'content_items', ['domain', 'level'])
    op.create_index('idx_ci_author', 'content_items', ['author_id'])
    op.create_index('idx_ci_tenant', 'content_items', ['tenant_id'])

    # content_likes
    op.create_table(
        'content_likes',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_id', sa.Integer, sa.ForeignKey('content_items.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_cl_user_content', 'content_likes', ['user_id', 'content_id'], unique=True)

    # content_bookmarks
    op.create_table(
        'content_bookmarks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_id', sa.Integer, sa.ForeignKey('content_items.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_cb_user_content', 'content_bookmarks', ['user_id', 'content_id'], unique=True)

    # content_comments
    op.create_table(
        'content_comments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_id', sa.Integer, sa.ForeignKey('content_items.id'), nullable=False),
        sa.Column('parent_id', sa.Integer, sa.ForeignKey('content_comments.id'), nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('like_count', sa.Integer, server_default='0'),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_cc_content_status', 'content_comments', ['content_id', 'status'])
    op.create_index('idx_cc_user', 'content_comments', ['user_id'])


def downgrade():
    op.drop_table('content_comments')
    op.drop_table('content_bookmarks')
    op.drop_table('content_likes')
    op.drop_table('content_items')
