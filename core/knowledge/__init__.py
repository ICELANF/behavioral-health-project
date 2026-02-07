"""
知识库 RAG 检索与引用系统

本地知识优先: 专家私有 (tenant +0.15) > 领域知识 (domain +0.08) > 平台公共 (platform +0)
"""

from .rag_middleware import rag_enhance, RAGEnhancedContext, record_citations
from .retriever import KnowledgeRetriever, RAGContext, AGENT_DOMAIN_MAP
from .embedding_service import EmbeddingService

__all__ = [
    "rag_enhance",
    "RAGEnhancedContext",
    "record_citations",
    "KnowledgeRetriever",
    "RAGContext",
    "AGENT_DOMAIN_MAP",
    "EmbeddingService",
]
