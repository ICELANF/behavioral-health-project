"""
XZBRxBridge — 专家处方注入适配器
将专家建议格式化为现有 RxComposer 可识别的 XZBRxFragment，
注入已验证的 BehaviorRx → 教练审核 → prescription_approved 流水线

铁律 I-06: requires_coach_review 始终为 True，不可绕过
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from xzb.models.xzb_models import (
    XZBRxFragment, XZBRxFragmentSchema, XZBConversation, XZBExpertProfile
)
from xzb.knowledge.retriever import RetrievalResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 触发信号类型（文档 §4.4）
# ─────────────────────────────────────────────

class TriggerSignalType:
    SEMANTIC    = "semantic"        # 受益者语义信号
    DEVICE_DATA = "device_data"     # 设备数据异常
    TTM_SHIFT   = "ttm_shift"       # TTM 阶段转换
    ADHERENCE   = "adherence"       # 依从性下降
    EXPERT_PUSH = "expert_push"     # 专家主动推送

@dataclass
class TriggerSignal:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


# ─────────────────────────────────────────────
# Trigger Detector
# ─────────────────────────────────────────────

class XZBTriggerDetector:
    """检测是否满足处方触发条件（文档 §4.4 五种触发信号）"""

    DEVICE_THRESHOLDS = {
        "cgm_postprandial_mmol": 10.0,   # CGM餐后峰值>10 连续3日
        "hrv_rmssd_ms": 20.0,            # HRV低于阈值
    }

    def detect(self, query: str, session_context: dict) -> Optional[TriggerSignal]:
        signals = []

        # 信号一：语义信号
        semantic_keywords = ["血糖", "控制不好", "吃药", "运动", "睡眠差"]
        hits = sum(1 for kw in semantic_keywords if kw in query)
        if hits >= 2:
            signals.append(TriggerSignal(
                type=TriggerSignalType.SEMANTIC,
                data={"matched_keywords": hits},
                confidence=min(0.4 + hits * 0.1, 0.9),
            ))

        # 信号二：设备数据异常
        device_data = session_context.get("device_data", {})
        device_anomalies = []
        for metric, threshold in self.DEVICE_THRESHOLDS.items():
            val = device_data.get(metric)
            if val and val > threshold:
                consecutive_days = session_context.get(f"{metric}_consecutive_days", 0)
                if consecutive_days >= 3:
                    device_anomalies.append(metric)
        if device_anomalies:
            signals.append(TriggerSignal(
                type=TriggerSignalType.DEVICE_DATA,
                data={"anomalies": device_anomalies},
                confidence=0.85,
            ))

        # 信号三：TTM 阶段转换
        prev_stage = session_context.get("prev_ttm_stage")
        curr_stage = session_context.get("ttm_stage")
        if prev_stage and curr_stage and prev_stage != curr_stage:
            signals.append(TriggerSignal(
                type=TriggerSignalType.TTM_SHIFT,
                data={"from": prev_stage, "to": curr_stage},
                confidence=0.90,
            ))

        # 信号四：依从性下降
        adherence_drop = session_context.get("adherence_consecutive_miss_days", 0)
        if adherence_drop >= 3:
            signals.append(TriggerSignal(
                type=TriggerSignalType.ADHERENCE,
                data={"miss_days": adherence_drop},
                confidence=0.80,
            ))

        if not signals:
            return None
        # 取置信度最高的信号
        return max(signals, key=lambda s: s.confidence)


# ─────────────────────────────────────────────
# XZBRxBridge
# ─────────────────────────────────────────────

class XZBRxBridge:
    """
    专家处方注入适配器（文档 §4.1 Step 6-7）

    职责：
    1. 判断当前情境是否满足专家处方适应症
    2. 生成 XZBRxFragment，作为 priority=0 来源注入 RxComposer
    3. 强制执行铁律：requires_coach_review=True
    """

    def __init__(self, rx_composer, template_repo):
        self.rx_composer = rx_composer        # 现有 RxComposerAgent
        self.template_repo = template_repo    # 专家处方模板库
        self.trigger_detector = XZBTriggerDetector()

    async def process(
        self,
        query: str,
        expert: XZBExpertProfile,
        seeker_id: UUID,
        retrieval_result: RetrievalResult,
        session_context: dict,
        conversation: XZBConversation,
        db: AsyncSession,
    ) -> Optional[XZBRxFragment]]:
        """
        处方桥接主流程（对应文档 §4.1 Step 6-9）
        """
        # Step 6: 判断是否触发处方
        signal = self.trigger_detector.detect(query, session_context)
        if signal is None:
            logger.debug("No trigger signal for expert %s seeker %s", expert.id, seeker_id)
            return None

        logger.info(
            "Trigger signal [%s] conf=%.2f for expert %s",
            signal.type, signal.confidence, expert.id
        )

        # Step 7: 生成处方片段草案
        fragment = await self._build_fragment(
            expert, seeker_id, retrieval_result, signal, session_context, conversation
        )

        # 持久化草案
        db.add(fragment)
        await db.flush()  # 获取 fragment.id

        # Step 8: 注入 RxComposer（priority=0，高于 BPT6(1) 和 BehaviorRx(2)）
        fragment_schema = XZBRxFragmentSchema(
            source="xzb_expert",
            expert_id=expert.id,
            expert_name=expert.display_name,
            priority=0,
            evidence_tier=fragment.evidence_tier,
            domain=fragment.domain,
            strategies=fragment.strategies,
            knowledge_refs=fragment.knowledge_refs or [],
            contraindications=fragment.contraindications or [],
            requires_coach_review=True,   # 铁律：不可修改
        )
        await self.rx_composer.inject_fragment(fragment_schema, seeker_id=seeker_id)

        # 标记对话已触发处方
        conversation.rx_triggered = True
        await db.commit()

        return fragment

    async def _build_fragment(
        self,
        expert: XZBExpertProfile,
        seeker_id: UUID,
        retrieval_result: RetrievalResult,
        signal: TriggerSignal,
        session_context: dict,
        conversation: XZBConversation,
    ) -> XZBRxFragment:
        """根据检索结果和触发信号构建处方片段"""

        # 从知识命中中找处方模板
        template_hits = [
            h for h in retrieval_result.knowledge_hits
            if h.type == "template"
        ]

        # 确定最高 evidence_tier
        all_tiers = [h.evidence_tier for h in retrieval_result.knowledge_hits if h.evidence_tier]
        best_tier = min(all_tiers, default="T3")   # T1 < T2 < T3 < T4 → min=最强证据

        # 构建策略列表（从模板或知识命中生成）
        strategies = []
        if template_hits:
            strategies = await self.template_repo.to_rx_strategies(
                template_hits[0].knowledge_id
            )
        elif retrieval_result.knowledge_hits:
            strategies = [
                {
                    "content": hit.content[:500],
                    "source_id": str(hit.knowledge_id),
                    "evidence_tier": hit.evidence_tier,
                }
                for hit in retrieval_result.knowledge_hits[:3]
            ]

        # 从适用条件中提取禁忌
        contraindications: List[str] = []
        for hit in retrieval_result.knowledge_hits:
            pass  # 从 applicable_conditions.contraindications 提取

        return XZBRxFragment(
            conversation_id=conversation.id,
            expert_id=expert.id,
            seeker_id=seeker_id,
            source="xzb_expert",
            priority=0,
            evidence_tier=best_tier,
            domain=_infer_domain(session_context, expert),
            strategies=strategies,
            knowledge_refs=[str(h.knowledge_id) for h in retrieval_result.knowledge_hits],
            style_profile_id=None,    # 由 XZBStyleAdapter 在输出时使用
            contraindications=contraindications,
            requires_coach_review=True,   # ← 铁律，不可修改
            status="draft",
        )

    async def expert_push(
        self,
        expert: XZBExpertProfile,
        seeker_id: UUID,
        rx_template_id: UUID,
        db: AsyncSession,
    ) -> XZBRxFragment:
        """
        信号五：专家主动推送处方草案（文档 §4.4 信号类型五）
        直接跳过触发判断，专家明确发起
        """
        strategies = await self.template_repo.to_rx_strategies(rx_template_id)
        fragment = XZBRxFragment(
            expert_id=expert.id,
            seeker_id=seeker_id,
            source="xzb_expert",
            priority=0,
            strategies=strategies,
            requires_coach_review=True,   # 铁律
            status="draft",
        )
        db.add(fragment)

        fragment_schema = XZBRxFragmentSchema(
            source="xzb_expert",
            expert_id=expert.id,
            expert_name=expert.display_name,
            priority=0,
            strategies=strategies,
            requires_coach_review=True,
        )
        await self.rx_composer.inject_fragment(fragment_schema, seeker_id=seeker_id)
        await db.commit()
        return fragment


def _infer_domain(session_context: dict, expert: XZBExpertProfile) -> str:
    """从会话上下文和专家领域标签推断处方领域"""
    tags = expert.domain_tags or []
    return tags[0] if tags else "general"
