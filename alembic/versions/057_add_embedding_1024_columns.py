"""add embedding 1024 columns (blue-green migration)

Revision ID: 057
Revises: 056
Create Date: 2026-02-26

蓝绿迁移: 在现有 768 维向量列旁新增 1024 维列，
双列并存期间旧列继续服务检索，新列用于重嵌入填充。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '057'
down_revision = '056'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- knowledge_chunks: 新增 1024 维列 ---
    op.add_column(
        'knowledge_chunks',
        sa.Column('embedding_1024', sa.Text(), nullable=True),
        # 注: 用 Text 列存 JSON 格式向量，与现有 retriever.py 的
        # json.loads() 路径一致；切换完成后再建 pgvector 原生索引
    )

    # --- xzb_knowledge: 新增 1024 维列 ---
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'xzb_knowledge'
                AND column_name = 'vector_embedding_1024'
            ) THEN
                ALTER TABLE xzb_knowledge
                ADD COLUMN vector_embedding_1024 vector(1024);
            END IF;
        END $$;
    """)

    # --- HNSW 索引 (xzb_knowledge, CONCURRENTLY 不阻塞读写) ---
    # 注意: Alembic 默认在事务中运行, CONCURRENTLY 需要 non-transactional
    # 所以这里用普通 CREATE INDEX
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_xzb_embedding_1024_cosine
        ON xzb_knowledge
        USING hnsw (vector_embedding_1024 vector_cosine_ops);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_xzb_embedding_1024_cosine;")
    op.execute("""
        ALTER TABLE xzb_knowledge
        DROP COLUMN IF EXISTS vector_embedding_1024;
    """)
    op.drop_column('knowledge_chunks', 'embedding_1024')
