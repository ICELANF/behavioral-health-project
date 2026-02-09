"""
测试 01 — 数据模型 & Schema 验证
运行: python tests/test_01_models.py

不需要数据库连接，纯 Python 单元测试。
验证: 模型定义完整性、枚举值、数据类序列化。
"""
import sys
import os
import unittest

# 把 backend 加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestKnowledgeModels(unittest.TestCase):
    """知识库模型定义测试"""

    def test_import_models(self):
        """能否导入知识库模型"""
        from models.knowledge import (
            KnowledgeDocument, KnowledgeChunk,
            KnowledgeDomain, KnowledgeCitation,
            DocStatus, KnowledgeScope,
        )
        self.assertTrue(hasattr(KnowledgeDocument, '__tablename__'))
        self.assertTrue(hasattr(KnowledgeChunk, '__tablename__'))

    def test_doc_status_enum(self):
        """DocStatus 枚举值"""
        from models.knowledge import DocStatus
        expected = {'pending', 'processing', 'ready', 'error'}
        actual = {s.value for s in DocStatus}
        self.assertEqual(expected, actual, f"DocStatus 缺少值: {expected - actual}")

    def test_visibility_scope_enum(self):
        """KnowledgeScope 枚举值"""
        from models.knowledge import KnowledgeScope
        expected = {'platform', 'domain', 'tenant'}
        actual = {s.value for s in KnowledgeScope}
        self.assertEqual(expected, actual, f"KnowledgeScope 缺少值: {expected - actual}")

    def test_table_names(self):
        """表名正确"""
        from models.knowledge import (
            KnowledgeDocument, KnowledgeChunk,
            KnowledgeDomain, KnowledgeCitation,
        )
        self.assertEqual(KnowledgeDocument.__tablename__, 'knowledge_documents')
        self.assertEqual(KnowledgeChunk.__tablename__, 'knowledge_chunks')
        self.assertEqual(KnowledgeDomain.__tablename__, 'knowledge_domains')
        self.assertEqual(KnowledgeCitation.__tablename__, 'knowledge_citations')

    def test_chunk_has_embedding_column(self):
        """KnowledgeChunk 必须有 embedding 列"""
        from models.knowledge import KnowledgeChunk
        cols = {c.name for c in KnowledgeChunk.__table__.columns}
        self.assertIn('embedding', cols, "缺少 embedding 列!")
        self.assertIn('scope', cols, "缺少 scope 列!")
        self.assertIn('tenant_id', cols, "缺少 tenant_id 列!")

    def test_document_has_priority(self):
        """KnowledgeDocument 必须有 priority 列 (RAG v2 排序依赖)"""
        from models.knowledge import KnowledgeDocument
        cols = {c.name for c in KnowledgeDocument.__table__.columns}
        self.assertIn('priority', cols, "缺少 priority 列 — RAG v2 的 boosted_score 需要此字段!")
        self.assertIn('is_active', cols, "缺少 is_active 列!")
        self.assertIn('status', cols, "缺少 status 列!")


class TestTenantModels(unittest.TestCase):
    """租户模型定义测试"""

    def test_import_tenant_models(self):
        """能否导入租户模型"""
        from models.tenant import ExpertTenant, TenantClient, TenantAgentMapping, TenantAuditLog
        self.assertTrue(hasattr(ExpertTenant, '__tablename__'))
        self.assertTrue(hasattr(TenantClient, '__tablename__'))
        self.assertTrue(hasattr(TenantAgentMapping, '__tablename__'))
        self.assertTrue(hasattr(TenantAuditLog, '__tablename__'))

    def test_tenant_table_names(self):
        """租户表名正确"""
        from models.tenant import ExpertTenant, TenantClient, TenantAgentMapping, TenantAuditLog
        self.assertEqual(ExpertTenant.__tablename__, 'expert_tenants')
        self.assertEqual(TenantClient.__tablename__, 'tenant_clients')
        self.assertEqual(TenantAgentMapping.__tablename__, 'tenant_agent_mappings')
        self.assertEqual(TenantAuditLog.__tablename__, 'tenant_audit_logs')


class TestRetrieverDataClasses(unittest.TestCase):
    """检索引擎数据类测试"""

    def test_citation_creation(self):
        """Citation 数据类创建和序列化"""
        from services.retriever import Citation, SourceType
        c = Citation(
            index=1,
            doc_title="测试文档",
            heading="第一章",
            author="张三",
            source="测试来源",
            page_number=5,
            relevance_score=0.85,
            content_preview="这是预览...",
            chunk_id=100,
            document_id=10,
            scope="tenant",
            source_type=SourceType.KNOWLEDGE,
        )
        d = c.to_dict()
        self.assertEqual(d["index"], 1)
        self.assertEqual(d["scope"], "tenant")
        self.assertEqual(d["scopeLabel"], "🔒 专家私有")
        self.assertEqual(d["sourceType"], "knowledge")
        self.assertIn("《测试文档》", d["label"])

    def test_citation_scope_labels(self):
        """所有 scope 都有正确的标签"""
        from services.retriever import Citation, SourceType
        for scope, expected_label in [
            ("tenant", "🔒 专家私有"),
            ("domain", "📂 领域知识"),
            ("platform", "🌐 平台公共"),
        ]:
            c = Citation(
                index=1, doc_title="T", heading="", author="",
                source="", page_number=None, relevance_score=0.5,
                content_preview="", chunk_id=1, document_id=1,
                scope=scope, source_type=SourceType.KNOWLEDGE,
            )
            self.assertEqual(c.scope_label, expected_label,
                             f"scope={scope} 标签不匹配")

    def test_rag_context_format_response(self):
        """RAGContext.format_response() 序列化完整性"""
        from services.retriever import Citation, RAGContext, SourceType
        citations = [
            Citation(1, "文档A", "", "", "", None, 0.9, "预览A", 1, 1, "tenant", SourceType.KNOWLEDGE),
            Citation(2, "文档B", "", "", "", None, 0.7, "预览B", 2, 2, "domain", SourceType.KNOWLEDGE),
        ]
        ctx = RAGContext(query="测试", citations=citations, prompt_injection="...", domains_searched=["tcm"])

        # 模拟 LLM 回复
        llm_response = "根据[1]所述，这个方法有效。[2]也提到了类似观点。\n\n【补充】一般认为还需要考虑季节因素。"
        result = ctx.format_response(llm_response)

        # 关键字段检查
        self.assertIn("text", result)
        self.assertIn("hasKnowledge", result)
        self.assertTrue(result["hasKnowledge"])
        self.assertIn("citationsUsed", result)
        self.assertEqual(result["citationsUsed"], [1, 2])
        self.assertIn("knowledgeCitations", result)
        self.assertIn("hasModelSupplement", result)
        self.assertTrue(result["hasModelSupplement"])
        self.assertIn("modelSupplementSections", result)
        self.assertTrue(len(result["modelSupplementSections"]) > 0)
        self.assertIn("sourceStats", result)
        self.assertIn("scopeBreakdown", result["sourceStats"])
        self.assertEqual(result["sourceStats"]["scopeBreakdown"]["tenant"], 1)
        self.assertEqual(result["sourceStats"]["scopeBreakdown"]["domain"], 1)

    def test_extract_model_supplements(self):
        """模型补充段落提取"""
        from services.retriever import RAGContext
        tests = [
            ("普通文本[1]。\n\n【补充】这是补充内容。", 1),
            ("回答[1]。\n\n【模型补充】额外说明。", 1),
            ("回答。\n\n**补充说明**: 通用知识。", 1),
            ("回答[1]。没有补充。", 0),
            ("【以下为通用专业知识，非本平台专属资料】\n通用内容。", 1),
        ]
        for text, expected_count in tests:
            sections = RAGContext._extract_model_supplements(text)
            self.assertEqual(len(sections), expected_count,
                             f"文本 '{text[:30]}...' 期望 {expected_count} 个补充段, 实际 {len(sections)}")

    def test_scope_boost_values(self):
        """scope 加权配置正确"""
        from services.retriever import SCOPE_BOOST
        self.assertGreater(SCOPE_BOOST["tenant"], SCOPE_BOOST["domain"])
        self.assertGreater(SCOPE_BOOST["domain"], SCOPE_BOOST["platform"])
        self.assertEqual(SCOPE_BOOST["platform"], 0.0)

    def test_agent_domain_map_completeness(self):
        """12 个 Agent 都有领域映射"""
        from services.retriever import AGENT_DOMAIN_MAP
        expected_agents = {
            "sleep", "glucose", "stress", "mental", "nutrition",
            "exercise", "tcm", "crisis", "motivation", "behavior_rx",
            "weight", "cardiac_rehab",
        }
        actual_agents = set(AGENT_DOMAIN_MAP.keys())
        missing = expected_agents - actual_agents
        self.assertEqual(len(missing), 0, f"AGENT_DOMAIN_MAP 缺少: {missing}")

        # 每个 Agent 至少有一个领域
        for agent_id, domains in AGENT_DOMAIN_MAP.items():
            self.assertTrue(len(domains) > 0, f"Agent {agent_id} 没有领域映射!")


class TestPromptInjection(unittest.TestCase):
    """Prompt 注入内容测试"""

    def test_build_injection_with_citations(self):
        """有引用时 prompt 包含关键指令"""
        from services.retriever import KnowledgeRetriever, Citation, SourceType

        # 创建 mock (不需要真正的 db 和 embedder)
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)

        citations = [
            Citation(1, "TCM指南", "体质辨识", "李时珍", "中医教材", 10, 0.9,
                     "体质分为九种...", 1, 1, "tenant", SourceType.KNOWLEDGE),
            Citation(2, "大五人格", "", "", "", None, 0.7,
                     "开放性是...", 2, 2, "domain", SourceType.KNOWLEDGE),
        ]

        # Mock rows — _build_injection expects tuples of (chunk, raw_score, boosted_score, doc)
        class MockChunk:
            def __init__(self, content):
                self.content = content
        class MockDoc:
            pass
        rows = [
            (MockChunk("体质分为九种：平和质、气虚质..."), 0.85, 0.9, MockDoc()),
            (MockChunk("开放性是大五人格的维度之一"), 0.65, 0.7, MockDoc()),
        ]

        prompt = retriever._build_injection(citations, rows)

        # 必须包含的关键指令
        self.assertIn("本地知识优先", prompt)
        self.assertIn("[1]", prompt)
        self.assertIn("[2]", prompt)
        self.assertIn("专家私有", prompt)
        self.assertIn("领域", prompt)
        self.assertIn("【补充】", prompt)
        self.assertIn("禁止编造", prompt)
        self.assertIn("以本地", prompt)  # "以本地资料为准"

    def test_build_no_knowledge_injection(self):
        """无知识命中时的提示"""
        from services.retriever import KnowledgeRetriever
        prompt = KnowledgeRetriever._build_no_knowledge_injection()
        self.assertIn("通用专业知识", prompt)
        self.assertIn("不要编造", prompt)


# ══════════════════════════════════════════
# V002 — 学分晋级体系模型
# ══════════════════════════════════════════

class TestV002CreditModels(unittest.TestCase):
    """V002 学分晋级体系 ORM 模型验证"""

    def test_import_v002_models(self):
        """能否导入V002四个ORM模型"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.models import CourseModule, UserCredit, CompanionRelation, PromotionApplication
        self.assertEqual(CourseModule.__tablename__, 'course_modules')
        self.assertEqual(UserCredit.__tablename__, 'user_credits')
        self.assertEqual(CompanionRelation.__tablename__, 'companion_relations')
        self.assertEqual(PromotionApplication.__tablename__, 'promotion_applications')

    def test_v002_enums(self):
        """V002 枚举值完整性"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.models import CompanionStatus, PromotionStatus
        self.assertEqual({s.value for s in CompanionStatus}, {'active', 'graduated', 'dropped'})
        self.assertEqual({s.value for s in PromotionStatus}, {'pending', 'approved', 'rejected'})

    def test_course_module_fields(self):
        """CourseModule 关键字段存在"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.models import CourseModule
        required_cols = ['id', 'code', 'title', 'module_type', 'tier', 'target_role',
                         'credit_value', 'sort_order', 'is_active']
        for col in required_cols:
            self.assertTrue(hasattr(CourseModule, col), f"CourseModule 缺少字段: {col}")

    def test_companion_relation_fields(self):
        """CompanionRelation 关键字段存在"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.models import CompanionRelation
        required_cols = ['id', 'mentor_id', 'mentee_id', 'mentor_role', 'mentee_role',
                         'status', 'quality_score', 'started_at', 'graduated_at']
        for col in required_cols:
            self.assertTrue(hasattr(CompanionRelation, col), f"CompanionRelation 缺少字段: {col}")

    def test_promotion_application_fields(self):
        """PromotionApplication 关键字段存在"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.models import PromotionApplication
        required_cols = ['id', 'user_id', 'from_role', 'to_role', 'status',
                         'credit_snapshot', 'point_snapshot', 'companion_snapshot',
                         'check_result', 'reviewer_id', 'reviewed_at']
        for col in required_cols:
            self.assertTrue(hasattr(PromotionApplication, col), f"PromotionApplication 缺少字段: {col}")

    def test_get_table_names_includes_v002(self):
        """get_table_names 包含V002表"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.models import get_table_names
        tables = get_table_names()
        for t in ['course_modules', 'user_credits', 'companion_relations', 'promotion_applications']:
            self.assertIn(t, tables, f"get_table_names() 缺少: {t}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
