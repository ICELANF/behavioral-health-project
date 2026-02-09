"""add knowledge_domains table and file_type/file_hash columns

Revision ID: 017
Revises: 016
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    # 1. knowledge_domains 表
    op.create_table(
        'knowledge_domains',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('domain_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 种子数据
    domains = [
        ('general', '通用', '通用健康知识'),
        ('tcm', '中医', '中医体质与养生'),
        ('nutrition', '营养', '营养学与膳食指导'),
        ('exercise', '运动', '运动康复与健身'),
        ('sleep', '睡眠', '睡眠科学与管理'),
        ('mental_health', '心理', '心理健康与情绪管理'),
        ('stress', '压力', '压力管理与应对策略'),
        ('metabolic', '代谢', '代谢疾病管理'),
        ('cardiac', '心脏', '心脏康复与心血管'),
        ('weight', '体重', '体重管理与减重'),
        ('motivation', '动机', '行为动机与激励'),
        ('behavior_change', '行为改变', '行为改变科学'),
        ('chronic_disease', '慢病', '慢性病管理'),
        ('geriatric', '老年', '老年健康管理'),
        ('big_five', '大五人格', '大五人格与健康干预'),
        ('psychology', '心理学', '心理学基础'),
        ('rehabilitation', '康复', '康复医学'),
    ]
    t = sa.table(
        'knowledge_domains',
        sa.column('domain_id', sa.String),
        sa.column('label', sa.String),
        sa.column('description', sa.Text),
    )
    for did, label, desc in domains:
        op.execute(t.insert().values(domain_id=did, label=label, description=desc))

    # 2. knowledge_documents 增加 file_type, file_hash 列
    op.add_column('knowledge_documents', sa.Column('file_type', sa.String(10), nullable=True))
    op.add_column('knowledge_documents', sa.Column('file_hash', sa.String(128), nullable=True))
    op.create_index('idx_kdoc_file_hash', 'knowledge_documents', ['file_hash'])


def downgrade():
    op.drop_index('idx_kdoc_file_hash', table_name='knowledge_documents')
    op.drop_column('knowledge_documents', 'file_hash')
    op.drop_column('knowledge_documents', 'file_type')
    op.drop_table('knowledge_domains')
