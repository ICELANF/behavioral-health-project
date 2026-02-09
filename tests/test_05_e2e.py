"""
测试 05 — 端到端流程
运行: python -m pytest tests/test_05_e2e.py -v

完整流程: 文档上传 → 解析 → 分块 → 向量化 → 入库 → 检索 → RAG 增强 → 前端展示格式

这是最重要的集成测试，验证所有组件串通。
需要: PostgreSQL + pgvector + Embedding 模型
"""
import sys, os, asyncio, unittest, tempfile, shutil
from unittest import IsolatedAsyncioTestCase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/health_platform"
)


class TestEndToEndIngestAndRetrieve(IsolatedAsyncioTestCase):
    """
    端到端: 文件 → 解析 → 分块 → 向量化 → 入库 → 检索

    完整验证 RAG v2 本地优先机制。
    """

    @classmethod
    def setUpClass(cls):
        """准备测试文件和服务"""
        cls.tmpdir = tempfile.mkdtemp(prefix="test_e2e_")

        # 创建测试知识文档 (中医体质)
        cls.test_doc_path = os.path.join(cls.tmpdir, "tcm_constitution.md")
        with open(cls.test_doc_path, "w", encoding="utf-8") as f:
            f.write("""# 中医体质辨识指南

## 九种体质概述

中医将人体体质分为九种基本类型：平和质、气虚质、阳虚质、阴虚质、
痰湿质、湿热质、血瘀质、气郁质、特禀质。

每种体质都有其独特的生理特征、心理特征和适宜的调理方法。

## 平和质

### 特征
阴阳气血调和，体态适中，面色红润，精力充沛。

### 调理建议
饮食均衡，适量运动，保持心情舒畅。

## 气虚质

### 特征
容易疲乏，气短，自汗，舌淡红，脉弱。

### 调理建议
补气为主，适宜食用黄芪、党参等补气食材。
避免过度劳累，适量运动如太极拳、八段锦。

## 阳虚质

### 特征
畏寒怕冷，手足不温，喜热饮食，舌淡胖嫩。

### 调理建议
温阳散寒，适宜食用生姜、桂圆、羊肉等温热食材。
注意保暖，避免受寒。
""")

        # 创建第二个测试文档 (大五人格)
        cls.test_doc2_path = os.path.join(cls.tmpdir, "big_five.md")
        with open(cls.test_doc2_path, "w", encoding="utf-8") as f:
            f.write("""# 大五人格与健康干预

## 开放性

高开放性人群倾向于接受新事物，对创新的健康方案接受度较高。
建议提供多样化的健康选择。

## 尽责性

高尽责性人群自律性强，适合结构化的健康管理计划。
可以设定明确的阶段目标和打卡机制。

## 外向性

外向性高的人群适合团体健康活动，社交支持有助于健康行为维持。
""")

        # 检查依赖
        try:
            from services.chunker import EmbeddingService
            cls.embedder = EmbeddingService()
            cls.embedding_available = True
        except Exception as e:
            cls.embedding_available = False
            cls.skip_reason = str(e)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    async def asyncSetUp(self):
        if not self.embedding_available:
            self.skipTest(f"Embedding 不可用: {self.skip_reason}")

        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        url = DATABASE_URL
        if "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(url, echo=False)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self._cleanup_doc_ids = []

    async def asyncTearDown(self):
        """清理测试数据"""
        if self._cleanup_doc_ids:
            from sqlalchemy import text
            async with self.engine.connect() as conn:
                for doc_id in self._cleanup_doc_ids:
                    await conn.execute(text("DELETE FROM knowledge_citations WHERE document_id = :id"), {"id": doc_id})
                    await conn.execute(text("DELETE FROM knowledge_chunks WHERE document_id = :id"), {"id": doc_id})
                    await conn.execute(text("DELETE FROM knowledge_documents WHERE id = :id"), {"id": doc_id})
                await conn.commit()
        if hasattr(self, 'engine'):
            await self.engine.dispose()

    async def test_full_ingest_pipeline(self):
        """完整入库流程: 文件 → 解析 → 分块 → 向量化 → 写入DB"""
        from services.ingest import KnowledgeIngestor

        async with self.SessionLocal() as session:
            ingestor = KnowledgeIngestor(db=session, embedder=self.embedder)
            doc_id = await ingestor.ingest_file(
                self.test_doc_path,
                scope="tenant",
                domain_id="tcm",
                tenant_id="test_tenant",
                author="测试作者",
                source_name="中医体质学",
                priority=8,
            )
            self._cleanup_doc_ids.append(doc_id)

            self.assertIsNotNone(doc_id, "入库失败! doc_id 为 None")
            self.assertGreater(doc_id, 0)

            # 验证数据库中有 chunks
            from sqlalchemy import text
            row = await session.execute(
                text("SELECT COUNT(*) FROM knowledge_chunks WHERE document_id = :id"),
                {"id": doc_id}
            )
            chunk_count = row.scalar()
            self.assertGreater(chunk_count, 0,
                               f"入库后 chunk 数为 0! doc_id={doc_id}")
            print(f"  ✅ 入库成功: doc_id={doc_id}, {chunk_count} chunks")

    async def test_ingest_dedup(self):
        """重复入库应去重 (相同文件哈希)"""
        from services.ingest import KnowledgeIngestor

        async with self.SessionLocal() as session:
            ingestor = KnowledgeIngestor(db=session, embedder=self.embedder)

            # 第一次入库
            doc_id1 = await ingestor.ingest_file(
                self.test_doc_path, scope="platform", domain_id="tcm",
            )
            self._cleanup_doc_ids.append(doc_id1)

            # 第二次入库同一文件
            doc_id2 = await ingestor.ingest_file(
                self.test_doc_path, scope="platform", domain_id="tcm",
            )
            if doc_id2 and doc_id2 != doc_id1:
                self._cleanup_doc_ids.append(doc_id2)

            # 应返回相同 doc_id 或跳过
            # (具体行为取决于实现: 返回已有 ID 或抛异常)
            print(f"  第一次: {doc_id1}, 第二次: {doc_id2}")
            if doc_id2 is not None:
                self.assertEqual(doc_id1, doc_id2,
                                 "重复入库应返回已有 doc_id 或跳过!")

    async def test_vector_search_after_ingest(self):
        """入库后向量检索能找到文档"""
        from services.ingest import KnowledgeIngestor
        from sqlalchemy import text

        async with self.SessionLocal() as session:
            ingestor = KnowledgeIngestor(db=session, embedder=self.embedder)
            doc_id = await ingestor.ingest_file(
                self.test_doc_path, scope="domain", domain_id="tcm",
                author="测试", priority=5,
            )
            self._cleanup_doc_ids.append(doc_id)

            # 用语义检索查找
            query_vec = self.embedder.embed("气虚体质调理方法")
            vec_str = str(query_vec)

            row = await session.execute(text(f"""
                SELECT c.content, c.heading, c.scope,
                       1.0 - (c.embedding <=> '{vec_str}'::vector(768)) AS score
                FROM knowledge_chunks c
                WHERE c.document_id = :doc_id
                ORDER BY score DESC
                LIMIT 3
            """), {"doc_id": doc_id})
            results = row.fetchall()

            self.assertTrue(len(results) > 0, "向量检索未返回结果!")

            # 最相关的结果应包含"气虚"相关内容
            top_content = results[0][0]
            top_score = results[0][3]
            print(f"  ✅ 检索到 {len(results)} 条, Top score={top_score:.3f}")
            print(f"     Top content: {top_content[:60]}...")

            self.assertGreater(top_score, 0.3,
                               f"最佳匹配分数过低: {top_score:.3f}")

    async def test_scope_priority_ordering(self):
        """RAG v2 核心: scope 优先级排序 (tenant > domain > platform)"""
        from services.ingest import KnowledgeIngestor
        from sqlalchemy import text
        import tempfile

        async with self.SessionLocal() as session:
            ingestor = KnowledgeIngestor(db=session, embedder=self.embedder)

            # 3 个不同文件 (不同hash), 相似内容, 入库到不同 scope
            scopes_config = [
                ("platform", "", 5, "体质辨识是中医基础理论 (平台版)"),
                ("domain", "", 5, "体质辨识是中医基础理论 (领域版)"),
                ("tenant", "test_tenant", 5, "体质辨识是中医基础理论 (专家版)"),
            ]

            for scope, tenant_id, priority, content in scopes_config:
                # 每个 scope 用独立文件 (不同 hash 避免去重)
                path = os.path.join(self.tmpdir, f"scope_test_{scope}.md")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"# 体质辨识 - {scope}\n\n{content}\n")
                doc_id = await ingestor.ingest_file(
                    path,
                    scope=scope, domain_id="tcm",
                    tenant_id=tenant_id, priority=priority,
                )
                self._cleanup_doc_ids.append(doc_id)

            # 用 RAG v2 的加权查询
            query_vec = self.embedder.embed("体质辨识")
            vec_str = str(query_vec)

            row = await session.execute(text(f"""
                SELECT c.scope,
                       1.0 - (c.embedding <=> '{vec_str}'::vector(768)) AS raw_score,
                       1.0 - (c.embedding <=> '{vec_str}'::vector(768))
                         + CASE c.scope
                             WHEN 'tenant' THEN 0.15
                             WHEN 'domain' THEN 0.08
                             ELSE 0.0
                           END AS boosted_score
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON d.id = c.document_id
                WHERE d.is_active = true
                  AND d.id IN ({','.join(str(i) for i in self._cleanup_doc_ids)})
                ORDER BY boosted_score DESC
                LIMIT 10
            """))
            results = row.fetchall()
            self.assertTrue(len(results) > 0)

            # 第一条应为 tenant scope
            self.assertEqual(results[0][0], 'tenant',
                             f"加权后 tenant 应排第一, 实际: {results[0][0]}")
            print(f"  ✅ Scope 排序正确: {[r[0] for r in results[:3]]}")


class TestRAGContextIntegration(unittest.TestCase):
    """RAGContext 集成测试 — 模拟完整 RAG 回复处理"""

    def test_full_response_processing(self):
        """模拟完整 RAG 回复解析流程"""
        from services.retriever import Citation, RAGContext, SourceType

        # 模拟检索到的引用
        citations = [
            Citation(1, "中医体质辨识指南", "九种体质", "王琦", "中医教材", 5,
                     0.92, "中医将人体体质分为九种...", 101, 10,
                     "tenant", SourceType.KNOWLEDGE),
            Citation(2, "大五人格应用", "开放性", "", "", None,
                     0.78, "高开放性人群...", 201, 20,
                     "domain", SourceType.KNOWLEDGE),
            Citation(3, "平台健康指南", "运动建议", "", "平台资料", None,
                     0.65, "每天至少30分钟...", 301, 30,
                     "platform", SourceType.KNOWLEDGE),
        ]

        ctx = RAGContext(
            query="气虚体质的人如何通过大五人格特征定制健康方案",
            citations=citations,
            prompt_injection="[模拟的prompt注入]",
            domains_searched=["tcm", "big_five"],
        )

        # 模拟 LLM 回复 (包含引用和模型补充)
        llm_response = """根据[1]所述，中医将人体体质分为九种基本类型，其中气虚质的特点是容易疲乏、气短、自汗。

针对气虚体质的调理，[1]建议补气为主，适宜食用黄芪、党参等补气食材，避免过度劳累。

在健康方案定制方面，[2]指出高开放性人群对创新方案接受度较高，可以引入多样化的调理选择。结合[3]的运动建议，适量运动对气虚体质很重要。

【补充】从现代营养学角度来看，气虚体质的人还应注意蛋白质摄入，保证每日优质蛋白供给。同时，适当补充B族维生素和铁元素有助于改善气虚症状。"""

        result = ctx.format_response(llm_response)

        # ── 验证完整响应结构 ──

        # 1. 基本字段
        self.assertIn("text", result)
        self.assertTrue(result["hasKnowledge"])
        self.assertEqual(result["citationsUsed"], [1, 2, 3])

        # 2. 知识库引用 (按 scope 分组)
        kc = result["knowledgeCitations"]
        self.assertEqual(len(kc), 3)
        scopes = [c["scope"] for c in kc]
        self.assertIn("tenant", scopes)
        self.assertIn("domain", scopes)
        self.assertIn("platform", scopes)

        # 3. 模型补充检测
        self.assertTrue(result["hasModelSupplement"])
        self.assertTrue(len(result["modelSupplementSections"]) > 0)
        self.assertIn("营养学", result["modelSupplementSections"][0])

        # 4. 来源统计
        stats = result["sourceStats"]
        self.assertEqual(stats["knowledgeCount"], 3)
        self.assertTrue(stats["modelSupplement"])
        self.assertEqual(stats["scopeBreakdown"]["tenant"], 1)
        self.assertEqual(stats["scopeBreakdown"]["domain"], 1)
        self.assertEqual(stats["scopeBreakdown"]["platform"], 1)

        print("  ✅ RAG 回复解析完整")
        print(f"     引用: {result['citationsUsed']}")
        print(f"     来源统计: {stats}")
        print(f"     模型补充: {len(result['modelSupplementSections'])} 段")

    def test_no_knowledge_response(self):
        """无知识库命中时的纯模型回复处理"""
        from services.retriever import RAGContext

        ctx = RAGContext(
            query="请问今天天气怎么样",
            citations=[], prompt_injection="", domains_searched=[],
        )

        llm_response = "【以下为通用专业知识，非本平台专属资料】\n抱歉，天气查询不在本平台知识范围内。"
        result = ctx.format_response(llm_response)

        self.assertFalse(result["hasKnowledge"])
        self.assertEqual(len(result["citationsUsed"]), 0)
        self.assertEqual(len(result["knowledgeCitations"]), 0)

    def test_mixed_citation_and_supplement(self):
        """混合引用和补充的边界情况"""
        from services.retriever import Citation, RAGContext, SourceType

        citations = [
            Citation(1, "文档A", "", "", "", None, 0.85, "内容A", 1, 1,
                     "tenant", SourceType.KNOWLEDGE),
        ]
        ctx = RAGContext(query="测试", citations=citations,
                         prompt_injection="", domains_searched=["tcm"])

        # 只用了 [1]，但有两处补充
        llm_response = "根据[1]的资料。\n\n【补充】额外信息1。\n\n【模型补充】额外信息2。"
        result = ctx.format_response(llm_response)

        self.assertEqual(result["citationsUsed"], [1])
        self.assertTrue(result["hasModelSupplement"])
        self.assertGreaterEqual(len(result["modelSupplementSections"]), 1)


class TestFrontendDataContract(unittest.TestCase):
    """前端数据契约验证 — 确保后端输出匹配前端期望"""

    def test_citation_dict_matches_vue_props(self):
        """Citation.to_dict() 输出匹配 CitationBlock.vue 的 props"""
        from services.retriever import Citation, SourceType

        c = Citation(1, "文档", "章节", "作者", "来源", 5, 0.9,
                     "预览...", 100, 10, "tenant", SourceType.KNOWLEDGE)
        d = c.to_dict()

        # CitationBlock.vue 的 citation 对象期望字段
        vue_expected = {
            "index", "label", "contentPreview", "relevanceScore",
            "scope", "scopeLabel", "sourceType",
        }
        for key in vue_expected:
            self.assertIn(key, d,
                          f"Citation.to_dict() 缺少前端需要的字段: {key}")

    def test_format_response_matches_vue_props(self):
        """format_response() 输出匹配 CitationBlock.vue 的完整 props"""
        from services.retriever import Citation, RAGContext, SourceType

        citations = [
            Citation(1, "T", "", "", "", None, 0.8, "P", 1, 1,
                     "tenant", SourceType.KNOWLEDGE),
        ]
        ctx = RAGContext("q", citations, "prompt", ["tcm"])
        result = ctx.format_response("回答[1]。\n\n【补充】额外。")

        # CitationBlock.vue v2 新增 props
        vue_props = [
            "knowledgeCitations",      # 仅知识库引用
            "hasModelSupplement",      # 是否有模型补充
            "modelSupplementSections", # 模型补充段落列表
            "sourceStats",             # 来源统计
        ]
        for prop in vue_props:
            self.assertIn(prop, result,
                          f"format_response 缺少前端 prop: {prop}")

        # sourceStats 结构
        stats = result["sourceStats"]
        for key in ["knowledgeCount", "modelSupplement", "scopeBreakdown"]:
            self.assertIn(key, stats,
                          f"sourceStats 缺少字段: {key}")

    def test_scope_label_format(self):
        """scope 标签格式与 CitationBlock.vue 样式一致"""
        from services.retriever import Citation, SourceType

        expected_labels = {
            "tenant": "🔒 专家私有",
            "domain": "📂 领域知识",
            "platform": "🌐 平台公共",
        }
        for scope, label in expected_labels.items():
            c = Citation(1, "T", "", "", "", None, 0.5, "", 1, 1,
                         scope, SourceType.KNOWLEDGE)
            self.assertEqual(c.scope_label, label,
                             f"scope={scope} 标签不匹配前端预期")


if __name__ == '__main__':
    unittest.main(verbosity=2)
