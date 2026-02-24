"""
XZBRxBridge — 专家处方注入适配器
将专家建议格式化为 XZBRxFragment, 注入现有 RxComposer 流水线

铁律 I-06: requires_coach_review 始终为 True，不可绕过

已适配: 同步 SQLAlchemy Session
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.xzb.xzb_models import (
    XZBRxFragment, XZBRxFragmentSchema, XZBConversation, XZBExpertProfile,
)
from core.xzb.xzb_retriever import RetrievalResult

logger = logging.getLogger(__name__)


class TriggerSignalType:
    SEMANTIC    = "semantic"
    DEVICE_DATA = "device_data"
    TTM_SHIFT   = "ttm_shift"
    ADHERENCE   = "adherence"
    EXPERT_PUSH = "expert_push"


@dataclass
class TriggerSignal:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


class XZBTriggerDetector:
    """检测是否满足处方触发条件 (5种触发信号)"""

    DEVICE_THRESHOLDS = {
        "cgm_postprandial_mmol": 10.0,
        "hrv_rmssd_ms": 20.0,
    }

    def detect(self, query: str, session_context: dict) -> Optional[TriggerSignal]:
        signals = []

        # 信号一: 语义信号
        semantic_keywords = ["血糖", "控制不好", "吃药", "运动", "睡眠差"]
        hits = sum(1 for kw in semantic_keywords if kw in query)
        if hits >= 2:
            signals.append(TriggerSignal(
                type=TriggerSignalType.SEMANTIC,
                data={"matched_keywords": hits},
                confidence=min(0.4 + hits * 0.1, 0.9),
            ))

        # 信号二: 设备数据异常
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

        # 信号三: TTM 阶段转换
        prev_stage = session_context.get("prev_ttm_stage")
        curr_stage = session_context.get("ttm_stage")
        if prev_stage and curr_stage and prev_stage != curr_stage:
            signals.append(TriggerSignal(
                type=TriggerSignalType.TTM_SHIFT,
                data={"from": prev_stage, "to": curr_stage},
                confidence=0.90,
            ))

        # 信号四: 依从性下降
        adherence_drop = session_context.get("adherence_consecutive_miss_days", 0)
        if adherence_drop >= 3:
            signals.append(TriggerSignal(
                type=TriggerSignalType.ADHERENCE,
                data={"miss_days": adherence_drop},
                confidence=0.80,
            ))

        if not signals:
            return None
        return max(signals, key=lambda s: s.confidence)


class XZBRxBridge:
    """专家处方注入适配器 (同步版)"""

    def __init__(self, rx_composer=None, template_repo=None):
        self.rx_composer = rx_composer
        self.template_repo = template_repo
        self.trigger_detector = XZBTriggerDetector()

    def process(
        self,
        query: str,
        expert: XZBExpertProfile,
        seeker_id: int,
        retrieval_result: RetrievalResult,
        session_context: dict,
        conversation: XZBConversation,
        db: Session,
    ) -> Optional[XZBRxFragment]:
        # 判断是否触发处方
        signal = self.trigger_detector.detect(query, session_context)
        if signal is None:
            return None

        logger.info(
            "XZB Trigger [%s] conf=%.2f for expert %s",
            signal.type, signal.confidence, expert.id,
        )

        # 生成处方片段草案
        fragment = self._build_fragment(
            expert, seeker_id, retrieval_result, signal, conversation,
        )
        db.add(fragment)
        db.flush()

        # 注入 RxComposer (priority=0, 高于 BPT6[1] 和 BehaviorRx[2])
        if self.rx_composer:
            try:
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
                    requires_coach_review=True,   # 铁律: 不可修改
                )
                self.rx_composer.inject_fragment(fragment_schema, seeker_id=seeker_id)
            except Exception as e:
                logger.error("XZB RxComposer inject failed: %s", e)

        # 铁律 I-06: 推入教练审批队列 (遵循 VisionGuard 成熟模式)
        self._queue_for_coach_review(fragment, expert, seeker_id, db)

        conversation.rx_triggered = True
        return fragment

    def _queue_for_coach_review(
        self, fragment: XZBRxFragment, expert: XZBExpertProfile,
        seeker_id: int, db: Session,
    ):
        """将处方片段推入教练审批队列 (铁律: AI→审核→推送)"""
        try:
            from core.coach_push_queue_service import create_queue_item

            # 解析教练ID: 通过 seeker 的 coach 绑定
            coach_id = self._resolve_coach_id(seeker_id, db)
            if not coach_id:
                logger.warning("XZB Rx: 无法找到 seeker %s 的教练, 跳过队列", seeker_id)
                return

            # seeker_id 是 INTEGER (users.id), 直接使用
            student_int_id = seeker_id
            if not student_int_id:
                logger.warning("XZB Rx: 无法解析 seeker %s 的用户ID", seeker_id)
                return

            # 构建审批条目内容
            import json
            strategies_text = "\n".join(
                f"- {s.get('content', '')[:200]}" for s in (fragment.strategies or [])[:5]
            )
            content = (
                f"【{expert.display_name}】行智诊疗建议\n"
                f"领域: {fragment.domain or '综合'}\n"
                f"循证等级: {fragment.evidence_tier or 'T3'}\n"
                f"策略:\n{strategies_text}"
            )

            create_queue_item(
                db=db,
                coach_id=coach_id,
                student_id=student_int_id,
                source_type="xzb_expert",
                source_id=str(fragment.id),
                title=f"行智诊疗处方 — {expert.display_name}",
                content=content,
                content_extra={
                    "xzb_fragment_id": str(fragment.id),
                    "expert_id": str(expert.id),
                    "domain": fragment.domain,
                    "evidence_tier": fragment.evidence_tier,
                    "strategies_count": len(fragment.strategies or []),
                },
                priority="normal",
            )
            logger.info(
                "XZB Rx fragment %s queued for coach %s review (student %s)",
                fragment.id, coach_id, student_int_id,
            )
        except ImportError:
            logger.debug("coach_push_queue_service not available, skipping queue")
        except Exception as e:
            logger.warning("XZB Rx coach queue failed (non-blocking): %s", e)

    def _resolve_coach_id(self, seeker_id: int, db: Session) -> int:
        """解析 seeker 绑定的教练ID (seeker_id 是 INTEGER users.id)"""
        try:
            from sqlalchemy import text as sa_text
            sid = seeker_id

            # 路径1: TenantClient → ExpertTenant → expert_user_id (即教练)
            row = db.execute(sa_text("""
                SELECT et.expert_user_id
                FROM tenant_clients tc
                JOIN expert_tenants et ON et.id = tc.tenant_id
                WHERE tc.user_id = :sid AND tc.status = 'active'
                LIMIT 1
            """), {"sid": sid}).first()
            if row:
                return row[0]

            # 路径2: 查找任意活跃教练 (兜底)
            row2 = db.execute(sa_text("""
                SELECT u.id FROM users u
                WHERE u.role::text IN ('COACH', 'SUPERVISOR', 'PROMOTER', 'MASTER', 'ADMIN')
                  AND u.is_active = TRUE
                LIMIT 1
            """)).first()
            return row2[0] if row2 else None
        except Exception:
            return None

    def _build_fragment(
        self, expert: XZBExpertProfile, seeker_id: int,
        retrieval_result: RetrievalResult, signal: TriggerSignal,
        conversation: XZBConversation,
    ) -> XZBRxFragment:
        # 确定最高 evidence_tier
        all_tiers = [h.evidence_tier for h in retrieval_result.knowledge_hits if h.evidence_tier]
        best_tier = min(all_tiers, default="T3")

        # 构建策略列表
        strategies = []
        template_hits = [h for h in retrieval_result.knowledge_hits if h.type == "template"]
        if template_hits:
            strategies = [{"content": template_hits[0].content[:500],
                           "source_id": str(template_hits[0].knowledge_id)}]
        elif retrieval_result.knowledge_hits:
            strategies = [
                {"content": h.content[:500], "source_id": str(h.knowledge_id),
                 "evidence_tier": h.evidence_tier}
                for h in retrieval_result.knowledge_hits[:3]
            ]

        return XZBRxFragment(
            conversation_id=conversation.id,
            expert_id=expert.id,
            seeker_id=seeker_id,
            source="xzb_expert",
            priority=0,
            evidence_tier=best_tier,
            domain=_infer_domain(expert),
            strategies=strategies,
            knowledge_refs=[h.knowledge_id for h in retrieval_result.knowledge_hits],
            requires_coach_review=True,   # 铁律
            status="draft",
        )


def _infer_domain(expert: XZBExpertProfile) -> str:
    tags = expert.domain_tags or []
    return tags[0] if tags else "general"
