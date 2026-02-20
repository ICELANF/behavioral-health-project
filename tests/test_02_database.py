"""
测试 02 — 数据库操作
运行: python -m pytest tests/test_02_database.py -v

需要 PostgreSQL + pgvector 运行。
验证: CRUD、向量检索、scope 过滤、Alembic 迁移一致性。
"""
import sys, os, asyncio, unittest
from unittest import IsolatedAsyncioTestCase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:difyai123456@host.docker.internal:5432/health_platform"
)


def get_async_engine():
    from sqlalchemy.ext.asyncio import create_async_engine
    url = DATABASE_URL
    if url.startswith("sqlite"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    elif "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return create_async_engine(url, echo=False)


class TestDatabaseConnection(IsolatedAsyncioTestCase):
    """基础连接 & pgvector"""

    async def test_connect(self):
        """能否建立数据库连接"""
        engine = get_async_engine()
        async with engine.connect() as conn:
            row = await conn.execute(
                __import__('sqlalchemy').text("SELECT 1 AS ok")
            )
            self.assertEqual(row.scalar(), 1)
        await engine.dispose()

    async def test_pgvector_extension(self):
        """pgvector 扩展已安装"""
        engine = get_async_engine()
        from sqlalchemy import text
        async with engine.connect() as conn:
            row = await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
            ver = row.scalar()
            self.assertIsNotNone(ver, "pgvector 扩展未安装!")
        await engine.dispose()

    async def test_vector_cosine_distance(self):
        """pgvector 余弦距离运算可用"""
        engine = get_async_engine()
        from sqlalchemy import text
        async with engine.connect() as conn:
            # 简单向量距离计算
            row = await conn.execute(
                text("SELECT '[1,0,0]'::vector(3) <=> '[0,1,0]'::vector(3) AS dist")
            )
            dist = row.scalar()
            self.assertIsNotNone(dist)
            self.assertGreater(dist, 0, "余弦距离应 > 0")
        await engine.dispose()


class TestKnowledgeTables(IsolatedAsyncioTestCase):
    """知识库表结构验证"""

    async def asyncSetUp(self):
        self.engine = get_async_engine()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_all_knowledge_tables_exist(self):
        """4张知识库表存在"""
        from sqlalchemy import text
        async with self.engine.connect() as conn:
            row = await conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE tablename IN (
                    'knowledge_documents', 'knowledge_chunks',
                    'knowledge_domains', 'knowledge_citations'
                )
                ORDER BY tablename
            """))
            tables = [r[0] for r in row.fetchall()]
            expected = ['knowledge_chunks', 'knowledge_citations',
                        'knowledge_documents', 'knowledge_domains']
            self.assertEqual(tables, expected,
                             f"缺少表: {set(expected) - set(tables)}")

    async def test_chunks_has_embedding_column(self):
        """knowledge_chunks 表有 embedding 向量列"""
        from sqlalchemy import text
        async with self.engine.connect() as conn:
            row = await conn.execute(text("""
                SELECT column_name, udt_name
                FROM information_schema.columns
                WHERE table_name = 'knowledge_chunks'
                  AND column_name = 'embedding'
            """))
            result = row.fetchone()
            self.assertIsNotNone(result, "knowledge_chunks 缺少 embedding 列!")
            # pgvector 列类型应为 'vector' 或 'USER-DEFINED'
            self.assertIn(result[1].lower(), ('vector', 'user-defined'),
                          f"embedding 列类型异常: {result[1]}")

    async def test_chunks_has_scope_column(self):
        """knowledge_chunks 有 scope 列 (RAG v2 必需)"""
        from sqlalchemy import text
        async with self.engine.connect() as conn:
            row = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'knowledge_chunks' AND column_name = 'scope'
            """))
            self.assertIsNotNone(row.fetchone(), "knowledge_chunks 缺少 scope 列!")

    async def test_documents_has_priority(self):
        """knowledge_documents 有 priority 列 (RAG v2 boosted_score 依赖)"""
        from sqlalchemy import text
        async with self.engine.connect() as conn:
            row = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'knowledge_documents' AND column_name = 'priority'
            """))
            self.assertIsNotNone(row.fetchone(), "knowledge_documents 缺少 priority 列!")


class TestDocumentCRUD(IsolatedAsyncioTestCase):
    """文档 CRUD (在临时数据上操作，测试后清理)"""

    async def asyncSetUp(self):
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        url = DATABASE_URL
        if url.startswith("sqlite"):
            url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(url, echo=False)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self._created_document_ids = []

    async def asyncTearDown(self):
        """清理测试数据"""
        if self._created_document_ids:
            from sqlalchemy import text
            async with self.engine.connect() as conn:
                for document_id in self._created_document_ids:
                    await conn.execute(
                        text("DELETE FROM knowledge_chunks WHERE document_id = :id"),
                        {"id": document_id}
                    )
                    await conn.execute(
                        text("DELETE FROM knowledge_documents WHERE id = :id"),
                        {"id": document_id}
                    )
                await conn.commit()
        await self.engine.dispose()

    async def test_insert_document(self):
        """插入文档记录"""
        from sqlalchemy import text
        async with self.engine.connect() as conn:
            row = await conn.execute(text("""
                INSERT INTO knowledge_documents
                    (title, file_type, file_hash, scope, domain_id, status, priority, is_active)
                VALUES
                    ('测试文档-单元测试', 'md', 'test_hash_001', 'platform', 'general', 'ready', 5, true)
                RETURNING id
            """))
            document_id = row.scalar()
            await conn.commit()
            self.assertIsNotNone(document_id)
            self._created_document_ids.append(document_id)

    async def test_insert_chunk_with_embedding(self):
        """插入带 embedding 的 chunk"""
        from sqlalchemy import text
        import json

        async with self.engine.connect() as conn:
            # 先插入文档
            row = await conn.execute(text("""
                INSERT INTO knowledge_documents
                    (title, file_type, file_hash, scope, domain_id, status, priority, is_active)
                VALUES
                    ('Embed测试文档', 'md', 'test_hash_002', 'domain', 'tcm', 'ready', 7, true)
                RETURNING id
            """))
            document_id = row.scalar()
            self._created_document_ids.append(document_id)

            # 插入 chunk (768 维零向量)
            zeros_768 = [0.0] * 768
            vec_str = str(zeros_768)  # pgvector 接受 Python 列表字符串形式
            await conn.execute(text(f"""
                INSERT INTO knowledge_chunks
                    (document_id, chunk_index, content, scope, embedding)
                VALUES
                    (:document_id, 0, '测试内容：体质辨识', 'domain',
                     '{vec_str}'::vector(768))
            """), {"document_id": document_id})
            await conn.commit()

            # 验证
            row = await conn.execute(text("""
                SELECT id, content FROM knowledge_chunks WHERE document_id = :document_id
            """), {"document_id": document_id})
            chunk = row.fetchone()
            self.assertIsNotNone(chunk, "chunk 插入失败!")
            self.assertIn('体质辨识', chunk[1])

    async def test_vector_search_returns_results(self):
        """向量检索能返回结果"""
        from sqlalchemy import text

        async with self.engine.connect() as conn:
            # 插入文档 + chunk
            row = await conn.execute(text("""
                INSERT INTO knowledge_documents
                    (title, file_type, file_hash, scope, domain_id, status, priority, is_active)
                VALUES ('向量检索测试', 'md', 'test_hash_003', 'platform', 'general', 'ready', 5, true)
                RETURNING id
            """))
            document_id = row.scalar()
            self._created_document_ids.append(document_id)

            # 插入一个非零向量
            vec = [0.01] * 768
            vec[0] = 1.0  # 使其非零
            vec_str = str(vec)
            await conn.execute(text(f"""
                INSERT INTO knowledge_chunks
                    (document_id, chunk_index, content, scope, embedding)
                VALUES
                    (:document_id, 0, '测试向量检索', 'platform',
                     '{vec_str}'::vector(768))
            """), {"document_id": document_id})
            await conn.commit()

            # 用相似向量检索
            query_vec = str(vec)
            row = await conn.execute(text(f"""
                SELECT c.id, c.content,
                       c.embedding <=> '{query_vec}'::vector(768) AS distance
                FROM knowledge_chunks c
                WHERE c.document_id = :document_id
                ORDER BY distance
                LIMIT 5
            """), {"document_id": document_id})
            results = row.fetchall()
            self.assertTrue(len(results) > 0, "向量检索无结果!")
            # 距离应接近 0 (自己检索自己)
            self.assertLess(results[0][2], 0.01, "自身向量距离应接近0!")


class TestScopeFiltering(IsolatedAsyncioTestCase):
    """scope 过滤 & 加权检索"""

    async def asyncSetUp(self):
        from sqlalchemy.ext.asyncio import create_async_engine
        url = DATABASE_URL
        if url.startswith("sqlite"):
            url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(url, echo=False)
        self._document_ids = []

    async def asyncTearDown(self):
        from sqlalchemy import text
        if self._document_ids:
            async with self.engine.connect() as conn:
                for document_id in self._document_ids:
                    await conn.execute(text("DELETE FROM knowledge_chunks WHERE document_id = :id"), {"id": document_id})
                    await conn.execute(text("DELETE FROM knowledge_documents WHERE id = :id"), {"id": document_id})
                await conn.commit()
        await self.engine.dispose()

    async def test_scope_boost_sql(self):
        """SQL 层面的 scope 加权排序 (RAG v2 核心逻辑)"""
        from sqlalchemy import text

        async with self.engine.connect() as conn:
            # 插入 3 个不同 scope 的文档+chunk
            scopes = [
                ("platform", 0.0, "平台公共内容"),
                ("domain",   0.08, "领域知识内容"),
                ("tenant",   0.15, "专家私有内容"),
            ]
            base_vec = [0.5] * 768

            for scope, boost, content in scopes:
                row = await conn.execute(text("""
                    INSERT INTO knowledge_documents
                        (title, file_type, file_hash, scope, domain_id, status, priority, is_active)
                    VALUES (:title, 'md', :hash, :scope, 'tcm', 'ready', 5, true)
                    RETURNING id
                """), {"title": f"scope测试-{scope}", "hash": f"scope_test_{scope}", "scope": scope})
                document_id = row.scalar()
                self._document_ids.append(document_id)

                vec_str = str(base_vec)
                await conn.execute(text(f"""
                    INSERT INTO knowledge_chunks
                        (document_id, chunk_index, content, scope, embedding)
                    VALUES (:document_id, 0, :content, :scope, '{vec_str}'::vector(768))
                """), {"document_id": document_id, "content": content, "scope": scope})

            await conn.commit()

            # 用 RAG v2 的 boosted_score SQL 查询
            query_vec = str(base_vec)
            rows = await conn.execute(text(f"""
                SELECT c.content, c.scope,
                       1.0 - (c.embedding <=> '{query_vec}'::vector(768)) AS raw_score,
                       1.0 - (c.embedding <=> '{query_vec}'::vector(768))
                         + CASE c.scope
                             WHEN 'tenant' THEN 0.15
                             WHEN 'domain' THEN 0.08
                             ELSE 0.0
                           END AS boosted_score
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON d.id = c.document_id
                WHERE d.is_active = true
                  AND d.status = 'ready'
                  AND d.id IN ({','.join(str(i) for i in self._document_ids)})
                ORDER BY boosted_score DESC
            """))
            results = rows.fetchall()
            self.assertEqual(len(results), 3, "应返回3条结果")

            # tenant 应排第一 (加权最高)
            self.assertEqual(results[0][1], 'tenant',
                             f"加权后 tenant 应排第一, 实际: {results[0][1]}")
            # domain 排第二
            self.assertEqual(results[1][1], 'domain',
                             f"加权后 domain 应排第二, 实际: {results[1][1]}")
            # platform 排第三
            self.assertEqual(results[2][1], 'platform',
                             f"加权后 platform 应排第三, 实际: {results[2][1]}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
