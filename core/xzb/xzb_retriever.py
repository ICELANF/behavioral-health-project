"""
XZBKnowledgeRetriever — 专家知识检索模块
检索优先级: 规则库精确匹配 → 专家私有向量 → 平台公共补充 → evidence_tier加权融合

已适配: 使用平台 core.models.Base ORM, 同步 SQLAlchemy Session
Phase 1: 对接平台 EmbeddingService + KnowledgeRetriever
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from core.xzb.xzb_models import XZBKnowledge, XZBKnowledgeRule

logger = logging.getLogger(__name__)

# 延迟导入平台 embedding_service (降级安全)
def _get_embedding_service():
    """获取平台 EmbeddingService 单例 (延迟导入, 降级安全)"""
    try:
        from core.knowledge.embedding_service import EmbeddingService
        return EmbeddingService()
    except ImportError:
        logger.debug("EmbeddingService not available")
        return None


# ─────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────

@dataclass
class RuleMatchResult:
    rule_id: UUID
    action_type: str
    action_content: str
    priority: int
    overrides_llm: bool
    source: str = "rule_engine"


@dataclass
class KnowledgeHit:
    knowledge_id: UUID
    content: str
    score: float
    evidence_tier: Optional[str]
    source_scope: str           # "expert" | "platform"
    type: str


@dataclass
class RetrievalResult:
    rule_match: Optional[RuleMatchResult] = None
    knowledge_hits: List[KnowledgeHit] = field(default_factory=list)
    total_hits: int = 0
    skipped_llm: bool = False


# evidence_tier 默认置信度
TIER_CONFIDENCE = {"T1": 0.95, "T2": 0.80, "T3": 0.65, "T4": 0.50}
SCOPE_BONUS = {"expert": 0.15, "domain": 0.08, "platform": 0.00}


# ─────────────────────────────────────────────
# Rule Engine
# ─────────────────────────────────────────────

class XZBRuleEngine:
    """精确规则匹配引擎"""

    def match(
        self,
        query: str,
        session_context: dict,
        expert_id: UUID,
        db: Session,
    ) -> Optional[RuleMatchResult]:
        rules = db.execute(
            select(XZBKnowledgeRule)
            .where(and_(
                XZBKnowledgeRule.expert_id == expert_id,
                XZBKnowledgeRule.is_active == True,  # noqa: E712
            ))
            .order_by(XZBKnowledgeRule.priority.desc())
        ).scalars().all()

        for rule in rules:
            if self._evaluate(rule.condition_json, query, session_context):
                return RuleMatchResult(
                    rule_id=rule.id,
                    action_type=rule.action_type,
                    action_content=rule.action_content,
                    priority=rule.priority,
                    overrides_llm=rule.overrides_llm,
                )
        return None

    def _evaluate(self, condition: dict, query: str, ctx: dict) -> bool:
        keywords = condition.get("trigger_keywords", [])
        if keywords and not any(kw in query for kw in keywords):
            return False

        thresholds = condition.get("device_data_thresholds", {})
        for metric, expr in thresholds.items():
            val = ctx.get("device_data", {}).get(metric)
            if val is None:
                continue
            try:
                op, threshold = expr[0], float(expr[1:])
                if op == ">" and not (val > threshold):
                    return False
                if op == "<" and not (val < threshold):
                    return False
            except (ValueError, IndexError):
                pass

        allowed_stages = condition.get("ttm_stage", [])
        if allowed_stages:
            if ctx.get("ttm_stage") not in allowed_stages:
                return False

        return True


# ─────────────────────────────────────────────
# Knowledge Retriever
# ─────────────────────────────────────────────

class XZBKnowledgeRetriever:
    """行智诊疗知识检索器 (同步 SQLAlchemy, 对接平台 embedding_service + rag_engine)"""

    def __init__(self, rag_engine=None, embed_service=None):
        self.rag_engine = rag_engine
        self.embed_service = embed_service
        self.rule_engine = XZBRuleEngine()

    def retrieve(
        self,
        query: str,
        expert_id: UUID,
        session_context: dict,
        db: Session,
        top_k_private: int = 3,
        top_k_public: int = 2,
        min_score: float = 0.35,
    ) -> RetrievalResult:
        result = RetrievalResult()

        # Step 1: 规则库精确匹配
        rule_match = self.rule_engine.match(query, session_context, expert_id, db)
        if rule_match:
            result.rule_match = rule_match
            if rule_match.overrides_llm:
                result.skipped_llm = True
                result.total_hits = 1
                logger.info("Rule %s overrides LLM for expert %s", rule_match.rule_id, expert_id)
                return result

        # Step 2: 私有知识向量检索
        private_hits = self._vector_search_private(
            query, expert_id, db, top_k=top_k_private, min_score=min_score
        )

        # Step 3: 平台公共知识补充
        public_hits = self._search_platform_knowledge(query, top_k=top_k_public, min_score=min_score, db=db)

        # Step 4: evidence_tier 加权融合
        all_hits = self._merge_with_tier_weighting(private_hits, public_hits)
        result.knowledge_hits = all_hits
        result.total_hits = len(all_hits)

        # 增加 usage_count
        self._increment_usage([h.knowledge_id for h in private_hits], db)

        return result

    def _vector_search_private(
        self, query: str, expert_id: UUID, db: Session,
        top_k: int = 3, min_score: float = 0.35,
    ) -> List[KnowledgeHit]:
        """pgvector 余弦相似度检索专家私有知识"""
        embed_svc = self.embed_service or _get_embedding_service()
        if not embed_svc:
            return []

        try:
            query_vector = embed_svc.embed_query(query)
            if not query_vector:
                logger.warning("XZB embed returned empty vector")
                return []
        except Exception as e:
            logger.warning("XZB embed failed: %s", e)
            return []

        try:
            from pgvector.sqlalchemy import cosine_distance
            rows = db.execute(
                select(
                    XZBKnowledge,
                    (1 - cosine_distance(XZBKnowledge.vector_embedding, query_vector)).label("score"),
                )
                .where(and_(
                    XZBKnowledge.expert_id == expert_id,
                    XZBKnowledge.is_active == True,  # noqa: E712
                    XZBKnowledge.expert_confirmed == True,  # noqa: E712
                    XZBKnowledge.vector_embedding.isnot(None),
                ))
                .order_by(cosine_distance(XZBKnowledge.vector_embedding, query_vector))
                .limit(top_k)
            ).all()
        except Exception as e:
            logger.warning("XZB vector search failed: %s", e)
            return []

        hits = []
        for row, score in rows:
            adjusted = score + SCOPE_BONUS["expert"]
            if adjusted < min_score:
                continue
            hits.append(KnowledgeHit(
                knowledge_id=row.id, content=row.content,
                score=adjusted, evidence_tier=row.evidence_tier,
                source_scope="expert", type=row.type,
            ))
        return hits

    def _search_platform_knowledge(
        self, query: str, top_k: int = 2, min_score: float = 0.35,
        db: Session = None,
    ) -> List[KnowledgeHit]:
        """
        平台公共知识检索。
        优先使用注入的 rag_engine; 回退到平台 KnowledgeRetriever (需 db + embed_service)
        """
        # 路径一: 注入的 rag_engine (原始接口)
        if self.rag_engine:
            try:
                public_hits = self.rag_engine.search(
                    query=query, scope="platform", top_k=top_k, min_score=min_score,
                )
                return [
                    KnowledgeHit(
                        knowledge_id=h.id, content=h.content, score=h.score,
                        evidence_tier=h.metadata.get("evidence_tier"),
                        source_scope="platform", type=h.metadata.get("type", "note"),
                    )
                    for h in public_hits
                ]
            except Exception as e:
                logger.warning("XZB platform RAG (injected) failed: %s", e)

        # 路径二: 平台 KnowledgeRetriever (Phase 1 对接)
        if not db:
            return []
        try:
            from core.knowledge.retriever import KnowledgeRetriever
            embed_svc = self.embed_service or _get_embedding_service()
            if not embed_svc:
                return []
            retriever = KnowledgeRetriever(db=db, embedder=embed_svc)
            rag_ctx = retriever.retrieve(
                query=query, agent_id="", tenant_id="",
                top_k=top_k, min_score=min_score,
            )
            return [
                KnowledgeHit(
                    knowledge_id=c.chunk_id, content=c.content_preview,
                    score=c.relevance_score,
                    evidence_tier=getattr(c, "evidence_tier", None),
                    source_scope="platform", type="knowledge",
                )
                for c in (rag_ctx.citations if rag_ctx else [])
            ]
        except Exception as e:
            logger.warning("XZB platform KnowledgeRetriever failed: %s", e)
            return []

    def _merge_with_tier_weighting(
        self, private_hits: List[KnowledgeHit], public_hits: List[KnowledgeHit],
    ) -> List[KnowledgeHit]:
        def weighted_score(hit: KnowledgeHit) -> float:
            tier_conf = TIER_CONFIDENCE.get(hit.evidence_tier or "T4", 0.50)
            scope_bonus = SCOPE_BONUS.get(hit.source_scope, 0.0)
            return hit.score * tier_conf + scope_bonus

        all_hits = private_hits + public_hits
        all_hits.sort(key=weighted_score, reverse=True)
        return all_hits

    def _increment_usage(self, knowledge_ids: List[UUID], db: Session):
        if not knowledge_ids:
            return
        from sqlalchemy import update
        db.execute(
            update(XZBKnowledge)
            .where(XZBKnowledge.id.in_(knowledge_ids))
            .values(usage_count=XZBKnowledge.usage_count + 1)
        )
