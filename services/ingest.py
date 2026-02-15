"""
知识入库服务

KnowledgeIngestor — 完整入库流程: 文件 → 解析 → 分块 → 向量化 → 写 DB
DOMAIN_SEEDS     — 预定义领域种子数据
"""
import sys, os
import hashlib
import logging
from typing import Optional

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from services.doc_parser import DocumentParser
from services.chunker import SmartChunker

logger = logging.getLogger(__name__)


# ── 领域种子数据 ──

DOMAIN_SEEDS = {
    "general":          {"label": "通用", "description": "通用健康知识"},
    "tcm":              {"label": "中医", "description": "中医体质与养生"},
    "nutrition":        {"label": "营养", "description": "营养学与膳食指导"},
    "exercise":         {"label": "运动", "description": "运动康复与健身"},
    "sleep":            {"label": "睡眠", "description": "睡眠科学与管理"},
    "mental_health":    {"label": "心理", "description": "心理健康与情绪管理"},
    "stress":           {"label": "压力", "description": "压力管理与应对策略"},
    "metabolic":        {"label": "代谢", "description": "代谢疾病管理"},
    "cardiac":          {"label": "心脏", "description": "心脏康复与心血管"},
    "weight":           {"label": "体重", "description": "体重管理与减重"},
    "motivation":       {"label": "动机", "description": "行为动机与激励"},
    "behavior_change":  {"label": "行为改变", "description": "行为改变科学"},
    "chronic_disease":  {"label": "慢病", "description": "慢性病管理"},
    "geriatric":        {"label": "老年", "description": "老年健康管理"},
    "big_five":         {"label": "大五人格", "description": "大五人格与健康干预"},
    "psychology":       {"label": "心理学", "description": "心理学基础"},
    "rehabilitation":   {"label": "康复", "description": "康复医学"},
}


# ── 入库服务 ──

class KnowledgeIngestor:
    """
    完整入库流程: 文件 → 解析 → 分块 → 向量化 → 写入 DB
    """

    def __init__(self, db, embedder):
        self.db = db
        self.embedder = embedder
        self.parser = DocumentParser()
        self.chunker = SmartChunker(max_tokens=512, overlap=50)

    async def ingest_file(
        self,
        file_path: str,
        scope: str = "platform",
        domain_id: str = "general",
        tenant_id: str = "",
        author: str = "",
        source_name: str = "",
        priority: int = 5,
    ) -> Optional[int]:
        """
        入库一个文件，返回 doc_id.
        重复文件 (相同 file_hash) 返回已有 doc_id.
        """
        from sqlalchemy import text

        # 1. 解析文件
        doc = self.parser.parse(file_path)

        # 2. 去重检查 (file_hash)
        row = await self.db.execute(
            text("SELECT id FROM knowledge_documents WHERE file_hash = :hash"),
            {"hash": doc.file_hash}
        )
        existing = row.scalar()
        if existing:
            logger.info(f"文档已存在 (hash={doc.file_hash[:16]}...), doc_id={existing}")
            return existing

        # 3. 插入文档记录
        row = await self.db.execute(
            text("""
                INSERT INTO knowledge_documents
                    (title, author, source, domain_id, scope, tenant_id,
                     priority, is_active, status, file_type, file_hash, chunk_count)
                VALUES
                    (:title, :author, :source, :domain_id, :scope, :tenant_id,
                     :priority, true, 'ready', :file_type, :file_hash, 0)
                RETURNING id
            """),
            {
                "title": doc.title, "author": author, "source": source_name,
                "domain_id": domain_id, "scope": scope, "tenant_id": tenant_id or None,
                "priority": priority, "file_type": doc.file_type, "file_hash": doc.file_hash,
            }
        )
        doc_id = row.scalar()

        # 4. 分块
        chunks = self.chunker.chunk(doc)
        if not chunks:
            logger.warning(f"文档 {doc.title} 未产生任何 chunk")
            await self.db.commit()
            return doc_id

        # 5. 向量化 + 写入 chunks
        import json
        texts = [c.content for c in chunks]
        vectors = self.embedder.embed_batch(texts)

        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            vec_json = json.dumps(vec) if vec else None
            await self.db.execute(
                text("""
                    INSERT INTO knowledge_chunks
                        (document_id, chunk_index, content, heading,
                         doc_title, doc_author, doc_source,
                         scope, domain_id, tenant_id, embedding)
                    VALUES
                        (:doc_id, :idx, :content, :heading,
                         :doc_title, :doc_author, :doc_source,
                         :scope, :domain_id, :tenant_id, :embedding)
                """),
                {
                    "doc_id": doc_id, "idx": i, "content": chunk.content,
                    "heading": chunk.heading, "doc_title": doc.title,
                    "doc_author": author, "doc_source": source_name,
                    "scope": scope, "domain_id": domain_id,
                    "tenant_id": tenant_id or None, "embedding": vec_json,
                }
            )

        # 更新 chunk_count
        await self.db.execute(
            text("UPDATE knowledge_documents SET chunk_count = :cnt WHERE id = :id"),
            {"cnt": len(chunks), "id": doc_id}
        )
        await self.db.commit()

        logger.info(f"入库完成: {doc.title} → doc_id={doc_id}, {len(chunks)} chunks")
        return doc_id


__all__ = ["KnowledgeIngestor", "DOMAIN_SEEDS"]
