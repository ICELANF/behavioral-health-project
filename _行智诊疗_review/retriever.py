"""
XZBKnowledgeRetriever
专家知识检索模块 — 插入现有 RAG 检索路径之前

检索优先级：
  1. 规则库精确匹配（overrides_llm=True → 直接返回，跳过 LLM）
  2. 专家私有知识向量检索（scope=expert, 天然 +0.15 加成）
  3. 平台公共知识补充（scope=platform）
  4. evidence_tier 加权融合
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from xzb.models.xzb_models import XZBKnowledge, XZBKnowledgeRule

logger = logging.getLogger(__name__)


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
    skipped_llm: bool = False   # True 当规则强制覆盖 LLM

# evidence_tier 默认置信度
TIER_CONFIDENCE = {"T1": 0.95, "T2": 0.80, "T3": 0.65, "T4": 0.50}

# 范围加成（复用平台现有机制）
SCOPE_BONUS = {"expert": 0.15, "domain": 0.08, "platform": 0.00}


# ─────────────────────────────────────────────
# Rule Engine
# ─────────────────────────────────────────────

class XZBRuleEngine:
    """
    精确规则匹配引擎
    condition_json 结构：
      {
        "trigger_keywords": ["血糖", "餐后"],   # 关键词任意命中
        "device_data_thresholds": {"cgm_postprandial_mmol": ">10"},
        "ttm_stage": ["S2", "S3"]              # TTM 阶段匹配
      }
    """

    async def match(
        self,
        query: str,
        session_context: dict,
        expert_id: UUID,
        db: AsyncSession,
    ) -> Optional[RuleMatchResult]:
        # 取该专家所有激活规则，按优先级降序
        result = await db.execute(
            select(XZBKnowledgeRule)
            .where(
                and_(
                    XZBKnowledgeRule.expert_id == expert_id,
                    XZBKnowledgeRule.is_active == True,  # noqa
                )
            )
            .order_by(XZBKnowledgeRule.priority.desc())
        )
        rules = result.scalars().all()

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
        # 1. 关键词匹配
        keywords = condition.get("trigger_keywords", [])
        if keywords:
            if not any(kw in query for kw in keywords):
                return False

        # 2. 设备数据阈值（如 CGM 餐后峰值）
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

        # 3. TTM 阶段匹配
        allowed_stages = condition.get("ttm_stage", [])
        if allowed_stages:
            current_stage = ctx.get("ttm_stage")
            if current_stage not in allowed_stages:
                return False

        return True


# ─────────────────────────────────────────────
# Knowledge Retriever
# ─────────────────────────────────────────────

class XZBKnowledgeRetriever:
    """
    行诊智伴知识检索器
    在现有 RAG 检索之前插入，作为 core/knowledge/ 的子模块运行
    """

    def __init__(self, rag_engine, embed_service):
        self.rag_engine = rag_engine
        self.embed_service = embed_service
        self.rule_engine = XZBRuleEngine()

    async def retrieve(
        self,
        query: str,
        expert_id: UUID,
        session_context: dict,
        db: AsyncSession,
        top_k_private: int = 3,
        top_k_public: int = 2,
        min_score: float = 0.35,
    ) -> RetrievalResult:
        """
        主检索入口 — 对应文档 §3.3 XZBKnowledgeRetriever

        流程：
          Step 1: 规则库精确匹配（优先于向量检索）
          Step 2: 私有知识向量检索（scope=expert, +0.15加成）
          Step 3: 平台公共知识补充（scope=platform）
          Step 4: evidence_tier 加权融合
        """
        result = RetrievalResult()

        # ── Step 1: 规则库精确匹配 ──────────────────────────────
        rule_match = await self.rule_engine.match(query, session_context, expert_id, db)
        if rule_match:
            result.rule_match = rule_match
            if rule_match.overrides_llm:
                result.skipped_llm = True
                result.total_hits = 1
                logger.info(
                    "Rule %s overrides LLM for expert %s", rule_match.rule_id, expert_id
                )
                return result   # 直接返回，跳过 LLM 和向量检索

        # ── Step 2: 私有知识向量检索 ────────────────────────────
        query_vector = await self.embed_service.embed(query)

        private_hits = await self._vector_search_private(
            query_vector, expert_id, db, top_k=top_k_private, min_score=min_score
        )

        # ── Step 3: 平台公共知识补充 ────────────────────────────
        public_hits = await self.rag_engine.search(
            query=query,
            scope="platform",
            top_k=top_k_public,
            min_score=min_score,
        )
        public_knowledge_hits = [
            KnowledgeHit(
                knowledge_id=h.id,
                content=h.content,
                score=h.score,
                evidence_tier=h.metadata.get("evidence_tier"),
                source_scope="platform",
                type=h.metadata.get("type", "note"),
            )
            for h in public_hits
        ]

        # ── Step 4: evidence_tier 加权融合 ──────────────────────
        all_hits = self._merge_with_tier_weighting(private_hits, public_knowledge_hits)
        result.knowledge_hits = all_hits
        result.total_hits = len(all_hits)

        # 增加 usage_count
        await self._increment_usage(
            [h.knowledge_id for h in private_hits if h.source_scope == "expert"], db
        )

        return result

    async def _vector_search_private(
        self,
        query_vector: list,
        expert_id: UUID,
        db: AsyncSession,
        top_k: int,
        min_score: float,
    ) -> List[KnowledgeHit]:
        """
        pgvector 余弦相似度检索专家私有知识
        利用平台范围加成机制（scope=expert, +0.15）
        """
        from pgvector.sqlalchemy import cosine_distance  # 需要 pgvector >= 0.3

        result = await db.execute(
            select(
                XZBKnowledge,
                (1 - cosine_distance(XZBKnowledge.vector_embedding, query_vector)).label("score"),
            )
            .where(
                and_(
                    XZBKnowledge.expert_id == expert_id,
                    XZBKnowledge.is_active == True,   # noqa
                    XZBKnowledge.expert_confirmed == True,
                    XZBKnowledge.vector_embedding.isnot(None),
                )
            )
            .order_by("score DESC")
            .limit(top_k)
        )
        rows = result.all()

        hits = []
        for row, score in rows:
            # 应用专家范围加成
            adjusted_score = score + SCOPE_BONUS["expert"]
            if adjusted_score < min_score:
                continue
            hits.append(
                KnowledgeHit(
                    knowledge_id=row.id,
                    content=row.content,
                    score=adjusted_score,
                    evidence_tier=row.evidence_tier,
                    source_scope="expert",
                    type=row.type,
                )
            )
        return hits

    def _merge_with_tier_weighting(
        self,
        private_hits: List[KnowledgeHit],
        public_hits: List[KnowledgeHit],
    ) -> List[KnowledgeHit]:
        """
        私有知识优先 + evidence_tier 加权排序
        """
        def weighted_score(hit: KnowledgeHit) -> float:
            tier_conf = TIER_CONFIDENCE.get(hit.evidence_tier or "T4", 0.50)
            scope_bonus = SCOPE_BONUS.get(hit.source_scope, 0.0)
            return hit.score * tier_conf + scope_bonus

        all_hits = private_hits + public_hits
        all_hits.sort(key=weighted_score, reverse=True)
        return all_hits

    async def _increment_usage(self, knowledge_ids: List[UUID], db: AsyncSession):
        if not knowledge_ids:
            return
        from sqlalchemy import update
        await db.execute(
            update(XZBKnowledge)
            .where(XZBKnowledge.id.in_(knowledge_ids))
            .values(usage_count=XZBKnowledge.usage_count + 1)
        )
        await db.commit()
