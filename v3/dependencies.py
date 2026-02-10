"""
依赖注入 — 全局单例管理
放置: api/dependencies.py

所有 LLM/RAG/Pipeline 实例在应用启动时创建一次,
通过 FastAPI Depends() 注入到路由中。
"""
import os
from functools import lru_cache

from core.llm.client import LLMClient
from core.llm.router import LLMRouter
from core.llm.coach_agent import CoachAgent
from core.rag.vector_store import QdrantStore
from core.rag.pipeline import RAGPipeline, RAGConfig
from core.rag.knowledge_loader import KnowledgeLoader
from core.diagnostic_pipeline import DiagnosticPipeline


@lru_cache()
def get_llm_client() -> LLMClient:
    return LLMClient()


@lru_cache()
def get_llm_router() -> LLMRouter:
    return LLMRouter(get_llm_client())


@lru_cache()
def get_qdrant_store() -> QdrantStore:
    url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
    return QdrantStore(base_url=url)


@lru_cache()
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline(
        get_llm_client(),
        get_llm_router(),
        get_qdrant_store(),
        RAGConfig(),
    )


@lru_cache()
def get_coach_agent() -> CoachAgent:
    return CoachAgent(
        llm_client=get_llm_client(),
        router=get_llm_router(),
        rag_pipeline=get_rag_pipeline(),
    )


@lru_cache()
def get_knowledge_loader() -> KnowledgeLoader:
    return KnowledgeLoader(get_llm_client(), get_qdrant_store())


def get_diagnostic_pipeline():
    """每次请求新建 (需要 db session)"""
    return DiagnosticPipeline()
