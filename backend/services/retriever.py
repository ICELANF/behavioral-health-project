"""
Bridge: services.retriever → core.knowledge.retriever

  from services.retriever import Citation, RAGContext, SourceType, ...
"""
import sys, os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.knowledge.retriever import (
    Citation,
    RAGContext,
    SourceType,
    SCOPE_BOOST,
    AGENT_DOMAIN_MAP,
    KnowledgeRetriever,
    build_rag_prompt,
)

__all__ = [
    "Citation",
    "RAGContext",
    "SourceType",
    "SCOPE_BOOST",
    "AGENT_DOMAIN_MAP",
    "KnowledgeRetriever",
    "build_rag_prompt",
]
