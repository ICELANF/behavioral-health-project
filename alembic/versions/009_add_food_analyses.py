"""add food analyses table

Revision ID: 009
Revises: 008
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'food_analyses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('food_name', sa.String(200), nullable=True),
        sa.Column('calories', sa.Float(), nullable=True),
        sa.Column('protein', sa.Float(), nullable=True),
        sa.Column('fat', sa.Float(), nullable=True),
        sa.Column('carbs', sa.Float(), nullable=True),
        sa.Column('fiber', sa.Float(), nullable=True),
        sa.Column('advice', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('meal_type', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_food_analyses_user_id', 'food_analyses', ['user_id'])


def downgrade():
    op.drop_index('idx_food_analyses_user_id', table_name='food_analyses')
    op.drop_table('food_analyses')
