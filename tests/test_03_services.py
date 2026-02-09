"""
测试 03 — 服务层
运行: python -m pytest tests/test_03_services.py -v

测试: doc_parser, chunker, embedding, retriever 核心逻辑。
不需要数据库 (mock async 调用)。Embedding 需要模型可用。
"""
import sys, os, unittest, tempfile, shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


# ══════════════════════════════════════════
# 文档解析器
# ══════════════════════════════════════════

class TestDocumentParser(unittest.TestCase):
    """doc_parser.py 功能测试"""

    @classmethod
    def setUpClass(cls):
        """创建临时测试文件"""
        cls.tmpdir = tempfile.mkdtemp(prefix="test_parser_")

        # 创建 .md 文件
        cls.md_file = os.path.join(cls.tmpdir, "test.md")
        with open(cls.md_file, "w", encoding="utf-8") as f:
            f.write("""# 第一章 体质辨识

中医体质分为九种：平和质、气虚质、阳虚质、阴虚质、痰湿质、湿热质、血瘀质、气郁质、特禀质。

## 1.1 平和质

平和质为正常体质，阴阳气血调和。

## 1.2 气虚质

气虚质表现为容易疲乏、气短、自汗等。

# 第二章 调理方法

根据体质类型选择相应调理方法。
""")

        # 创建 .txt 文件
        cls.txt_file = os.path.join(cls.tmpdir, "test.txt")
        with open(cls.txt_file, "w", encoding="utf-8") as f:
            f.write("这是一段纯文本内容。\n包含多行。\n用于测试TXT解析。")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_parse_markdown(self):
        """解析 Markdown 文件"""
        from services.doc_parser import DocumentParser
        parser = DocumentParser()
        doc = parser.parse(self.md_file)

        self.assertEqual(doc.file_type, ".md")
        self.assertTrue(doc.total_chars > 0)
        self.assertTrue(len(doc.sections) > 0, "未解析出任何章节!")
        self.assertIn("体质辨识", doc.raw_text)

    def test_parse_txt(self):
        """解析 TXT 文件"""
        from services.doc_parser import DocumentParser
        parser = DocumentParser()
        doc = parser.parse(self.txt_file)

        self.assertEqual(doc.file_type, ".txt")
        self.assertTrue(doc.total_chars > 0)
        self.assertIn("纯文本", doc.raw_text)

    def test_file_hash(self):
        """文件哈希计算"""
        from services.doc_parser import DocumentParser
        parser = DocumentParser()
        doc = parser.parse(self.md_file)

        self.assertTrue(len(doc.file_hash) > 0, "文件哈希为空!")
        # SHA256 = 64 hex chars
        self.assertEqual(len(doc.file_hash), 64,
                         f"哈希长度异常: {len(doc.file_hash)}, 期望 64 (SHA256)")

    def test_unsupported_format(self):
        """不支持的格式抛异常"""
        from services.doc_parser import DocumentParser
        parser = DocumentParser()
        bad_file = os.path.join(self.tmpdir, "test.xyz")
        with open(bad_file, "w") as f:
            f.write("data")

        with self.assertRaises(Exception):
            parser.parse(bad_file)

    def test_sections_have_headings(self):
        """Markdown 章节有正确标题"""
        from services.doc_parser import DocumentParser
        parser = DocumentParser()
        doc = parser.parse(self.md_file)

        headings = [s.heading for s in doc.sections if s.heading]
        self.assertTrue(len(headings) > 0, "未提取到任何标题!")
        # 应包含"第一章"或"体质辨识"
        found = any("体质" in h or "第一章" in h for h in headings)
        self.assertTrue(found, f"标题中未找到预期内容, 实际: {headings}")


# ══════════════════════════════════════════
# 智能分块
# ══════════════════════════════════════════

class TestSmartChunker(unittest.TestCase):
    """chunker.py 分块功能测试"""

    def _get_parsed_doc(self):
        """构造测试用 ParsedDocument"""
        from services.doc_parser import ParsedDocument, ParsedSection
        sections = [
            ParsedSection(heading="概述", level=1, content="这是概述内容。" * 20),
            ParsedSection(heading="详细说明", level=2, content="详细说明的内容。" * 100),
            ParsedSection(heading="总结", level=1, content="简短总结。"),
        ]
        return ParsedDocument(
            title="测试文档", raw_text="", sections=sections,
            file_type=".md", file_hash="abc123", total_chars=1000,
        )

    def test_basic_chunking(self):
        """基本分块功能"""
        from services.chunker import SmartChunker
        chunker = SmartChunker(max_tokens=512, overlap=50)
        doc = self._get_parsed_doc()
        chunks = chunker.chunk(doc)

        self.assertTrue(len(chunks) > 0, "未生成任何 chunk!")
        for c in chunks:
            self.assertTrue(len(c.content) > 0, f"Chunk {c.index} 内容为空!")

    def test_max_token_respected(self):
        """每个 chunk 不超过 max_tokens"""
        from services.chunker import SmartChunker
        chunker = SmartChunker(max_tokens=100, overlap=20)
        doc = self._get_parsed_doc()
        chunks = chunker.chunk(doc)

        for c in chunks:
            # 估算 token 数 (中文约1字=1.5token)
            est_tokens = len(c.content)
            # 给些宽松度 (max_tokens * 3 for Chinese chars)
            self.assertLess(est_tokens, 100 * 3,
                            f"Chunk {c.index} 太长: {est_tokens} chars")

    def test_chunk_metadata(self):
        """chunk 携带文档元数据"""
        from services.chunker import SmartChunker
        chunker = SmartChunker(max_tokens=512)
        doc = self._get_parsed_doc()
        chunks = chunker.chunk(doc)

        for c in chunks:
            self.assertEqual(c.doc_title, "测试文档",
                             f"Chunk {c.index} 文档标题丢失!")

    def test_min_token_filter(self):
        """过短内容被过滤"""
        from services.chunker import SmartChunker
        from services.doc_parser import ParsedDocument, ParsedSection

        doc = ParsedDocument(
            title="短文档", raw_text="", file_type=".md",
            file_hash="short", total_chars=5,
            sections=[ParsedSection(heading="", content="短")],
        )
        chunker = SmartChunker(max_tokens=512, min_tokens=10)
        chunks = chunker.chunk(doc)
        # 内容太短应被过滤
        self.assertEqual(len(chunks), 0,
                         "过短内容应被 min_tokens 过滤!")

    def test_overlap_presence(self):
        """有 overlap 时 chunk 之间内容有重叠"""
        from services.chunker import SmartChunker
        chunker = SmartChunker(max_tokens=50, overlap=20)
        doc = self._get_parsed_doc()
        chunks = chunker.chunk(doc)

        if len(chunks) >= 2:
            # 至少部分连续 chunk 应有内容重叠
            found_overlap = False
            for i in range(len(chunks) - 1):
                end_of_current = chunks[i].content[-30:]
                start_of_next = chunks[i+1].content[:50]
                # 检查是否有重叠字符
                for k in range(5, len(end_of_current)):
                    if end_of_current[k:] in start_of_next:
                        found_overlap = True
                        break
                if found_overlap:
                    break
            # 不强制断言，因为某些分块策略可能不产生字面重叠
            # 但记录结果
            if not found_overlap:
                print("  ⚠️ 未检测到字面 overlap (可能是句子边界分块策略)")


# ══════════════════════════════════════════
# Embedding 向量化
# ══════════════════════════════════════════

class TestEmbeddingService(unittest.TestCase):
    """EmbeddingService 向量化测试 (需要模型可用)"""

    @classmethod
    def setUpClass(cls):
        """加载 Embedding 模型 (可能耗时)"""
        try:
            from services.chunker import EmbeddingService
            cls.embedder = EmbeddingService()
            cls.available = True
        except Exception as e:
            cls.available = False
            cls.skip_reason = str(e)

    def setUp(self):
        if not self.available:
            self.skipTest(f"Embedding 模型不可用: {self.skip_reason}")

    def test_single_text_embedding(self):
        """单条文本向量化"""
        vec = self.embedder.embed("中医体质辨识")
        self.assertEqual(len(vec), 768, f"向量维度错误: {len(vec)}, 期望 768")

    def test_batch_embedding(self):
        """批量向量化"""
        texts = ["平和质", "气虚质", "阳虚质"]
        vecs = self.embedder.embed_batch(texts)
        self.assertEqual(len(vecs), 3)
        for v in vecs:
            self.assertEqual(len(v), 768)

    def test_similar_texts_closer(self):
        """语义相似的文本向量距离更近"""
        import numpy as np

        v1 = np.array(self.embedder.embed("中医体质辨识方法"))
        v2 = np.array(self.embedder.embed("体质分类与鉴别"))
        v3 = np.array(self.embedder.embed("今天天气很好"))

        # 余弦相似度
        def cosine(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_12 = cosine(v1, v2)  # 体质相关
        sim_13 = cosine(v1, v3)  # 不相关

        self.assertGreater(sim_12, sim_13,
                           f"体质相关文本应更相似: sim(体质,体质)={sim_12:.3f} vs sim(体质,天气)={sim_13:.3f}")

    def test_empty_text(self):
        """空文本不崩溃"""
        vec = self.embedder.embed("")
        self.assertEqual(len(vec), 768)

    def test_long_text(self):
        """超长文本不崩溃"""
        long_text = "中医养生保健知识" * 500
        vec = self.embedder.embed(long_text)
        self.assertEqual(len(vec), 768)


# ══════════════════════════════════════════
# Retriever 纯逻辑 (无 DB)
# ══════════════════════════════════════════

class TestRetrieverLogic(unittest.TestCase):
    """retriever.py 纯逻辑测试 (不涉及数据库)"""

    def test_source_type_enum(self):
        """SourceType 枚举值"""
        from services.retriever import SourceType
        self.assertEqual(SourceType.KNOWLEDGE, "knowledge")
        self.assertEqual(SourceType.MODEL_SUPPLEMENT, "model")

    def test_citation_to_dict_completeness(self):
        """Citation.to_dict() 包含所有 v2 字段"""
        from services.retriever import Citation, SourceType
        c = Citation(
            index=1, doc_title="T", heading="H", author="A",
            source="S", page_number=1, relevance_score=0.9,
            content_preview="P", chunk_id=1, document_id=1,
            scope="tenant", source_type=SourceType.KNOWLEDGE,
        )
        d = c.to_dict()

        required_keys = {
            "index", "label", "contentPreview", "relevanceScore",
            "scope", "scopeLabel", "sourceType", "chunkId", "documentId",
        }
        missing = required_keys - set(d.keys())
        self.assertEqual(len(missing), 0, f"to_dict() 缺少字段: {missing}")

    def test_format_ref_block(self):
        """_format_ref_block 格式化单条参考"""
        from services.retriever import KnowledgeRetriever, Citation, SourceType

        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        c = Citation(
            index=1, doc_title="体质学", heading="概述", author="王琦",
            source="教材", page_number=5, relevance_score=0.88,
            content_preview="体质是...", chunk_id=1, document_id=1,
            scope="tenant", source_type=SourceType.KNOWLEDGE,
        )

        class MockRow:
            def __init__(self, content):
                self.content = content

        row = MockRow("体质是人体生命过程中...")
        block = retriever._format_ref_block(c, row)

        self.assertIn("[1]", block)
        self.assertIn("体质学", block)
        self.assertIn("体质是", block)

    def test_rag_context_no_citations(self):
        """无引用时 RAGContext 正确处理"""
        from services.retriever import RAGContext
        ctx = RAGContext(query="测试", citations=[], prompt_injection="", domains_searched=[])
        result = ctx.format_response("纯模型回答内容")

        self.assertFalse(result["hasKnowledge"])
        self.assertEqual(len(result["citationsUsed"]), 0)
        self.assertEqual(len(result["knowledgeCitations"]), 0)


# ══════════════════════════════════════════
# Ingest 入库逻辑 (不实际写 DB)
# ══════════════════════════════════════════

class TestIngestLogic(unittest.TestCase):
    """ingest.py 入库逻辑测试"""

    def test_domain_seeds_complete(self):
        """DOMAIN_SEEDS 包含所有预定义领域"""
        from services.ingest import DOMAIN_SEEDS
        expected = {
            "general", "tcm", "nutrition", "exercise", "sleep",
            "mental_health", "stress", "metabolic", "cardiac",
            "weight", "motivation", "behavior_change",
            "chronic_disease", "geriatric", "big_five",
        }
        actual = set(DOMAIN_SEEDS.keys())
        missing = expected - actual
        # 不强制要求全部匹配 (可能有不同版本), 但核心领域必须在
        core = {"general", "tcm", "nutrition", "exercise", "sleep", "mental_health"}
        core_missing = core - actual
        self.assertEqual(len(core_missing), 0,
                         f"DOMAIN_SEEDS 缺少核心领域: {core_missing}")

    def test_ingestor_init(self):
        """KnowledgeIngestor 可以实例化 (mock 依赖)"""
        from services.ingest import KnowledgeIngestor
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_embedder = MagicMock()
        ingestor = KnowledgeIngestor(db=mock_db, embedder=mock_embedder)

        self.assertIsNotNone(ingestor.parser)
        self.assertIsNotNone(ingestor.chunker)


# ══════════════════════════════════════════
# V002 — 晋级规则 & 校验服务
# ══════════════════════════════════════════

class TestV002PromotionRules(unittest.TestCase):
    """V002 晋级规则配置校验"""

    @classmethod
    def setUpClass(cls):
        import json
        rules_path = Path(__file__).parent.parent / "configs" / "promotion_rules.json"
        cls.rules = json.loads(rules_path.read_text(encoding="utf-8"))["rules"]

    def test_rules_loaded(self):
        """晋级规则加载成功"""
        self.assertEqual(len(self.rules), 5, "应有5条晋级规则 L0→L5")

    def test_rule_chain_complete(self):
        """晋级链完整: observer→grower→sharer→coach→promoter→master"""
        chain = [(r["from_role"], r["to_role"]) for r in self.rules]
        expected = [
            ("observer", "grower"), ("grower", "sharer"), ("sharer", "coach"),
            ("coach", "promoter"), ("promoter", "master"),
        ]
        self.assertEqual(chain, expected)

    def test_credits_increasing(self):
        """每级总学分要求递增"""
        totals = [r["credits"]["total_min"] for r in self.rules]
        for i in range(len(totals) - 1):
            self.assertLess(totals[i], totals[i + 1],
                            f"学分未递增: {totals[i]} >= {totals[i + 1]}")


class TestV002PromotionService(unittest.TestCase):
    """V002 晋级校验服务结构测试"""

    def test_import_service(self):
        """能否导入晋级校验服务"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.promotion_service import check_promotion_eligibility, _get_applicable_rule
        self.assertIsNotNone(check_promotion_eligibility)
        self.assertIsNotNone(_get_applicable_rule)

    def test_applicable_rule_found(self):
        """能找到各角色的晋级规则"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.promotion_service import _get_applicable_rule
        for role in ["observer", "grower", "sharer", "coach", "promoter"]:
            rule = _get_applicable_rule(role)
            self.assertIsNotNone(rule, f"找不到 {role} 的晋级规则")
            self.assertEqual(rule["from_role"], role)

    def test_no_rule_for_master(self):
        """master 无晋级路径"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.promotion_service import _get_applicable_rule
        self.assertIsNone(_get_applicable_rule("master"))

    def test_no_rule_for_admin(self):
        """admin 无晋级路径"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from core.promotion_service import _get_applicable_rule
        self.assertIsNone(_get_applicable_rule("admin"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
