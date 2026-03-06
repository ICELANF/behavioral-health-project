"""
Agent 对话 RAG 中间件 (同步版)

胶水层: 在调用 LLM 之前检索知识 → 注入 prompt → 包装回复 + 引用数据。

用法:
    from core.knowledge import rag_enhance, record_citations

    enhanced = rag_enhance(db, "糖尿病能吃水果吗", agent_id="nutrition")
    response = llm.chat(system=enhanced.system_prompt, ...)
    result = enhanced.wrap_response(response.text)
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────
# 增强结果
# ──────────────────────────────────────────

@dataclass
class RAGEnhancedContext:
    """RAG 增强后的上下文"""
    system_prompt: str
    has_knowledge: bool = False
    citation_count: int = 0
    domains_searched: List[str] = field(default_factory=list)
    _rag_context: Any = None

    def wrap_response(self, llm_response: str) -> Dict[str, Any]:
        """包装 LLM 回复 + 引用数据"""
        if self._rag_context:
            return self._rag_context.format_response(llm_response)

        model_sections = re.findall(
            r'【(?:补充|模型补充|补充说明|以下为通用专业知识[^】]*)】\s*(.+?)(?=\n\n|$)',
            llm_response, re.DOTALL
        )

        return {
            "text": llm_response,
            "hasKnowledge": False,
            "citationsUsed": [],
            "citations": [],
            "knowledgeCitations": [],
            "hasModelSupplement": len(model_sections) > 0 or not self._rag_context,
            "modelSupplementSections": [s.strip() for s in model_sections if s.strip()],
            "allCitations": [],
            "domainsSearched": self.domains_searched,
            "sourceStats": {
                "knowledgeCount": 0,
                "modelSupplement": True,
                "scopeBreakdown": {},
            },
        }


# ──────────────────────────────────────────
# 全局 Embedder 单例
# ──────────────────────────────────────────

_embedder_instance = None

def _get_embedder():
    """懒加载 Embedding 服务 (全局单例)"""
    global _embedder_instance
    if _embedder_instance is None:
        from .embedding_service import EmbeddingService
        _embedder_instance = EmbeddingService()
        logger.info(
            "✅ RAG Embedding 服务已加载 (provider=%s, model=%s, %d维)",
            _embedder_instance.provider, _embedder_instance.model, _embedder_instance.expected_dim,
        )
    return _embedder_instance


# ──────────────────────────────────────────
# 核心函数: rag_enhance
# ──────────────────────────────────────────

def rag_enhance(
    db: Session,
    query: str,
    agent_id: str = "",
    tenant_id: str = "",
    base_system_prompt: str = "",
    persona: dict = None,
    top_k: int = 5,
    min_score: float = 0.35,
) -> RAGEnhancedContext:
    """
    一站式 RAG 增强 (同步版)

    输入: 用户问题 + Agent/租户上下文 + 原始系统提示
    输出: 增强后的系统提示 + 引用包装器
    """
    from .retriever import KnowledgeRetriever, build_rag_prompt

    embedder = _get_embedder()
    retriever = KnowledgeRetriever(db, embedder)

    rag_context = retriever.retrieve(
        query=query,
        agent_id=agent_id,
        tenant_id=tenant_id,
        top_k=top_k,
        min_score=min_score,
    )

    system_prompt = build_rag_prompt(base_system_prompt, rag_context, persona)

    if rag_context.has_knowledge:
        logger.info(
            f"📚 RAG: {agent_id}@{tenant_id} → "
            f"找到 {len(rag_context.citations)} 条, "
            f"领域 {rag_context.domains_searched}"
        )

    return RAGEnhancedContext(
        system_prompt=system_prompt,
        has_knowledge=rag_context.has_knowledge,
        citation_count=len(rag_context.citations),
        domains_searched=rag_context.domains_searched,
        _rag_context=rag_context,
    )


# ──────────────────────────────────────────
# 引用记录 (审计追踪)
# ──────────────────────────────────────────

def record_citations(
    db: Session,
    enhanced: RAGEnhancedContext,
    llm_response: str,
    session_id: str = "",
    message_id: str = "",
    agent_id: str = "",
    tenant_id: str = "",
    user_id: str = "",
):
    """记录引用到 knowledge_citations 表"""
    if not enhanced._rag_context or not enhanced._rag_context.has_knowledge:
        return

    from core.models import KnowledgeCitation

    used_indexes = set(int(r) for r in re.findall(r'\[(\d+)\]', llm_response))

    for cite in enhanced._rag_context.citations:
        if cite.index not in used_indexes:
            continue

        record = KnowledgeCitation(
            session_id=session_id,
            message_id=message_id,
            agent_id=agent_id,
            tenant_id=tenant_id,
            user_id=user_id,
            chunk_id=cite.chunk_id,
            document_id=cite.document_id,
            query_text=enhanced._rag_context.query[:500],
            relevance_score=cite.relevance_score,
            rank_position=cite.index,
            citation_text=cite.content_preview[:500],
            citation_label=cite.label,
        )
        db.add(record)

    try:
        db.commit()
        logger.info(f"📝 引用记录: {len(used_indexes)} 条写入 citations 表")
    except Exception as e:
        db.rollback()
        logger.error(f"引用记录写入失败: {e}")
