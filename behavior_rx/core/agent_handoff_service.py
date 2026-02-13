"""
BehaviorOS — AgentHandoffService Agent 交接协议服务
====================================================
管理 4 款 Expert Agent 之间的交接:
  - 阶段提升: Coach → 领域 Agent (S2→S3)
  - 阶段回退: 领域 Agent → Coach (回退)
  - 横切面: 任意 → Adherence (依从性问题)
  - 紧急接管: 任意 → Coach (自我效能崩塌)
  - 领域协同: Metabolic ↔ Cardiac (共病)

交接协议字段:
  rx_context, rx_conflict, adherence_overlay, escalation, outcome
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .rx_schemas import (
    ExpertAgentType,
    HandoffContext,
    HandoffRequest,
    HandoffResponse,
    HandoffStatus,
    HandoffType,
    RxPrescriptionDTO,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 交接规则配置
# =====================================================================

# 交接资格矩阵: 从哪个Agent → 到哪个Agent 是否允许
HANDOFF_ELIGIBILITY = {
    # Coach 可以交接到任何领域 Agent
    (ExpertAgentType.BEHAVIOR_COACH, ExpertAgentType.METABOLIC_EXPERT): True,
    (ExpertAgentType.BEHAVIOR_COACH, ExpertAgentType.CARDIAC_EXPERT): True,
    (ExpertAgentType.BEHAVIOR_COACH, ExpertAgentType.ADHERENCE_EXPERT): True,
    # 领域 Agent 可以回交给 Coach
    (ExpertAgentType.METABOLIC_EXPERT, ExpertAgentType.BEHAVIOR_COACH): True,
    (ExpertAgentType.CARDIAC_EXPERT, ExpertAgentType.BEHAVIOR_COACH): True,
    (ExpertAgentType.ADHERENCE_EXPERT, ExpertAgentType.BEHAVIOR_COACH): True,
    # 领域 Agent 之间的协同
    (ExpertAgentType.METABOLIC_EXPERT, ExpertAgentType.CARDIAC_EXPERT): True,
    (ExpertAgentType.CARDIAC_EXPERT, ExpertAgentType.METABOLIC_EXPERT): True,
    # 任何 Agent 可以触发 Adherence (横切面)
    (ExpertAgentType.METABOLIC_EXPERT, ExpertAgentType.ADHERENCE_EXPERT): True,
    (ExpertAgentType.CARDIAC_EXPERT, ExpertAgentType.ADHERENCE_EXPERT): True,
    # Adherence 可以协同回领域 Agent
    (ExpertAgentType.ADHERENCE_EXPERT, ExpertAgentType.METABOLIC_EXPERT): True,
    (ExpertAgentType.ADHERENCE_EXPERT, ExpertAgentType.CARDIAC_EXPERT): True,
}

# 阶段提升交接的最低要求
STAGE_PROMOTION_THRESHOLD = {
    "min_stage": 3,          # 最低 S3 才能交接到领域 Agent
    "min_readiness": 0.6,    # 最低就绪度
    "min_stability": 0.5,    # 最低稳定度
}

# 阶段回退交接的触发条件
STAGE_REGRESSION_TRIGGER = {
    "stage_drop": 2,         # 阶段下降 ≥2 级触发
    "efficacy_floor": 0.2,   # 自我效能 < 0.2 触发
    "stability_floor": 0.3,  # 稳定度 < 0.3 触发
}


# =====================================================================
# AgentHandoffService
# =====================================================================

class AgentHandoffService:
    """
    Agent 交接协议服务

    使用方式:
        service = AgentHandoffService()

        # 检查是否需要交接
        should, handoff_type, target = service.check_handoff_needed(
            current_agent, context, rx
        )

        # 发起交接
        if should:
            request = HandoffRequest(...)
            response = await service.initiate_handoff(request, db)
    """

    def __init__(self):
        logger.info("AgentHandoffService initialized")

    # ---------------------------------------------------------------
    # 交接检测 — 是否需要交接
    # ---------------------------------------------------------------

    def check_handoff_needed(
        self,
        current_agent: ExpertAgentType,
        context: HandoffContext,
        current_rx: Optional[RxPrescriptionDTO] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[HandoffType], Optional[ExpertAgentType]]:
        """
        检测是否需要 Agent 交接

        Args:
            current_agent: 当前 Agent 类型
            context: 交接上下文
            current_rx: 当前处方
            metrics: 附加指标 {medication_missed, exercise_fear_score, ...}

        Returns:
            (should_handoff, handoff_type, target_agent)
        """
        metrics = metrics or {}

        # ---- 规则 1: 阶段提升 → Coach→领域 Agent ----
        if current_agent == ExpertAgentType.BEHAVIOR_COACH:
            if self._check_stage_promotion(context):
                target = self._select_domain_agent(context, metrics)
                return True, HandoffType.STAGE_PROMOTION, target

        # ---- 规则 2: 阶段回退 → 领域 Agent→Coach ----
        if current_agent != ExpertAgentType.BEHAVIOR_COACH:
            if self._check_stage_regression(context):
                return True, HandoffType.STAGE_REGRESSION, ExpertAgentType.BEHAVIOR_COACH

        # ---- 规则 3: 自我效能崩塌 → 紧急接管 ----
        if self._check_efficacy_collapse(context):
            return True, HandoffType.EMERGENCY_TAKEOVER, ExpertAgentType.BEHAVIOR_COACH

        # ---- 规则 4: 依从性问题 → 横切面触发 Adherence ----
        if current_agent != ExpertAgentType.ADHERENCE_EXPERT:
            if self._check_adherence_issue(metrics):
                return True, HandoffType.CROSS_CUTTING, ExpertAgentType.ADHERENCE_EXPERT

        # ---- 规则 5: 领域协同 (共病) ----
        if current_agent in (ExpertAgentType.METABOLIC_EXPERT,
                             ExpertAgentType.CARDIAC_EXPERT):
            co_target = self._check_domain_coordination(current_agent, metrics)
            if co_target:
                return True, HandoffType.DOMAIN_COORDINATION, co_target

        return False, None, None

    def _check_stage_promotion(self, context: HandoffContext) -> bool:
        """检查是否满足阶段提升交接条件"""
        return (
            context.stage >= STAGE_PROMOTION_THRESHOLD["min_stage"]
            and context.readiness >= STAGE_PROMOTION_THRESHOLD["min_readiness"]
        )

    def _check_stage_regression(self, context: HandoffContext) -> bool:
        """检查是否发生阶段回退"""
        # 阶段太低, 需要回 Coach
        return context.stage <= 1

    def _check_efficacy_collapse(self, context: HandoffContext) -> bool:
        """检查自我效能是否崩塌"""
        # 通过 domain_state 中的 self_efficacy 判断
        efficacy = context.domain_state.get("self_efficacy", 0.5)
        stability = context.domain_state.get("stage_stability", 0.5)
        return (
            efficacy < STAGE_REGRESSION_TRIGGER["efficacy_floor"]
            and stability < STAGE_REGRESSION_TRIGGER["stability_floor"]
        )

    def _check_adherence_issue(self, metrics: Dict[str, Any]) -> bool:
        """检查是否存在依从性问题"""
        medication_missed = metrics.get("medication_missed_7d", 0)
        visit_overdue_days = metrics.get("visit_overdue_days", 0)
        overall_adherence = metrics.get("overall_adherence", 1.0)

        return (
            medication_missed >= 3
            or visit_overdue_days >= 14
            or overall_adherence < 0.5
        )

    def _check_domain_coordination(
        self, current_agent: ExpertAgentType, metrics: Dict[str, Any]
    ) -> Optional[ExpertAgentType]:
        """检查是否需要领域协同"""
        comorbidity = metrics.get("comorbidity", [])
        if current_agent == ExpertAgentType.METABOLIC_EXPERT:
            if "cardiovascular" in comorbidity:
                return ExpertAgentType.CARDIAC_EXPERT
        elif current_agent == ExpertAgentType.CARDIAC_EXPERT:
            if "metabolic_syndrome" in comorbidity:
                return ExpertAgentType.METABOLIC_EXPERT
        return None

    def _select_domain_agent(
        self, context: HandoffContext, metrics: Dict[str, Any]
    ) -> ExpertAgentType:
        """选择最合适的领域 Agent"""
        domain_state = context.domain_state
        primary_domain = domain_state.get("primary_domain", "metabolic")

        domain_map = {
            "metabolic": ExpertAgentType.METABOLIC_EXPERT,
            "cardiac": ExpertAgentType.CARDIAC_EXPERT,
            "adherence": ExpertAgentType.ADHERENCE_EXPERT,
        }
        return domain_map.get(primary_domain, ExpertAgentType.METABOLIC_EXPERT)

    # ---------------------------------------------------------------
    # 交接发起 & 管理
    # ---------------------------------------------------------------

    async def initiate_handoff(
        self,
        request: HandoffRequest,
        db=None,
    ) -> HandoffResponse:
        """
        发起 Agent 交接

        流程:
          1. 验证交接资格
          2. 准备交接上下文
          3. 记录交接日志
          4. 返回交接响应

        Args:
            request: 交接请求
            db: 数据库会话 (可选)

        Returns:
            HandoffResponse
        """
        # 1. 验证资格
        eligible = HANDOFF_ELIGIBILITY.get(
            (request.from_agent, request.to_agent), False
        )
        if not eligible:
            logger.warning(
                f"Handoff denied: {request.from_agent.value} → "
                f"{request.to_agent.value} not eligible"
            )
            return HandoffResponse(
                handoff_id=uuid.uuid4(),
                status=HandoffStatus.REJECTED,
                accepted=False,
                message=f"交接路径不被允许: {request.from_agent.value} → {request.to_agent.value}",
            )

        # 2. 交接条件验证
        if request.handoff_type == HandoffType.STAGE_PROMOTION:
            if not self._validate_promotion(request.rx_context):
                return HandoffResponse(
                    handoff_id=uuid.uuid4(),
                    status=HandoffStatus.REJECTED,
                    accepted=False,
                    message=f"阶段提升条件不满足: stage={request.rx_context.stage}, "
                            f"readiness={request.rx_context.readiness}",
                )

        # 3. 创建交接记录
        handoff_id = uuid.uuid4()

        if db is not None:
            await self._persist_handoff(handoff_id, request, db)

        logger.info(
            f"Handoff initiated: {handoff_id} "
            f"{request.from_agent.value} → {request.to_agent.value} "
            f"type={request.handoff_type.value} "
            f"user={request.user_id}"
        )

        return HandoffResponse(
            handoff_id=handoff_id,
            status=HandoffStatus.ACCEPTED,
            accepted=True,
            message=f"交接已接受: {request.from_agent.value} → {request.to_agent.value}",
        )

    def _validate_promotion(self, context: HandoffContext) -> bool:
        """验证阶段提升条件"""
        return (
            context.stage >= STAGE_PROMOTION_THRESHOLD["min_stage"]
            and context.readiness >= STAGE_PROMOTION_THRESHOLD["min_readiness"]
        )

    async def complete_handoff(
        self,
        handoff_id: uuid.UUID,
        outcome: Dict[str, Any],
        db=None,
    ) -> bool:
        """完成交接"""
        if db is not None:
            await self._update_handoff_status(
                handoff_id, HandoffStatus.COMPLETED, outcome, db
            )
        logger.info(f"Handoff completed: {handoff_id}")
        return True

    async def cancel_handoff(
        self,
        handoff_id: uuid.UUID,
        reason: str,
        db=None,
    ) -> bool:
        """取消交接"""
        if db is not None:
            await self._update_handoff_status(
                handoff_id, HandoffStatus.CANCELLED, {"reason": reason}, db
            )
        logger.info(f"Handoff cancelled: {handoff_id} reason={reason}")
        return True

    # ---------------------------------------------------------------
    # 持久化
    # ---------------------------------------------------------------

    async def _persist_handoff(
        self, handoff_id: uuid.UUID, request: HandoffRequest, db
    ) -> None:
        """持久化交接记录"""
        try:
            from .rx_models import AgentHandoffLog

            record = AgentHandoffLog(
                id=handoff_id,
                user_id=request.user_id,
                session_id=request.session_id,
                from_agent=request.from_agent.value,
                to_agent=request.to_agent.value,
                handoff_type=request.handoff_type.value,
                status=HandoffStatus.ACCEPTED.value,
                rx_context=request.rx_context.model_dump(mode="json"),
                rx_prescription_id=request.rx_prescription_id,
                trigger_reason=request.trigger_reason,
                trigger_data=request.trigger_data,
            )
            db.add(record)
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to persist handoff: {e}")

    async def _update_handoff_status(
        self,
        handoff_id: uuid.UUID,
        status: HandoffStatus,
        outcome: Dict[str, Any],
        db,
    ) -> None:
        """更新交接状态"""
        try:
            from .rx_models import AgentHandoffLog
            from sqlalchemy import update

            stmt = (
                update(AgentHandoffLog)
                .where(AgentHandoffLog.id == handoff_id)
                .values(
                    status=status.value,
                    outcome=outcome,
                    completed_at=datetime.utcnow() if status == HandoffStatus.COMPLETED else None,
                )
            )
            await db.execute(stmt)
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to update handoff status: {e}")

    # ---------------------------------------------------------------
    # 查询
    # ---------------------------------------------------------------

    async def get_user_handoffs(
        self,
        user_id: uuid.UUID,
        db,
        limit: int = 20,
        status_filter: Optional[HandoffStatus] = None,
    ) -> List[Dict[str, Any]]:
        """获取用户的交接历史"""
        try:
            from .rx_models import AgentHandoffLog
            from sqlalchemy import select

            query = (
                select(AgentHandoffLog)
                .where(AgentHandoffLog.user_id == user_id)
                .order_by(AgentHandoffLog.initiated_at.desc())
                .limit(limit)
            )
            if status_filter:
                query = query.where(AgentHandoffLog.status == status_filter.value)

            result = await db.execute(query)
            records = result.scalars().all()

            return [
                {
                    "id": str(r.id),
                    "from_agent": r.from_agent,
                    "to_agent": r.to_agent,
                    "handoff_type": r.handoff_type,
                    "status": r.status,
                    "trigger_reason": r.trigger_reason,
                    "rx_context": r.rx_context,
                    "outcome": r.outcome,
                    "initiated_at": r.initiated_at.isoformat() if r.initiated_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to get user handoffs: {e}")
            return []

    async def get_active_handoff(
        self,
        user_id: uuid.UUID,
        db,
    ) -> Optional[Dict[str, Any]]:
        """获取用户当前活跃的交接"""
        try:
            from .rx_models import AgentHandoffLog
            from sqlalchemy import select

            query = (
                select(AgentHandoffLog)
                .where(
                    AgentHandoffLog.user_id == user_id,
                    AgentHandoffLog.status.in_([
                        HandoffStatus.INITIATED.value,
                        HandoffStatus.ACCEPTED.value,
                        HandoffStatus.IN_PROGRESS.value,
                    ]),
                )
                .order_by(AgentHandoffLog.initiated_at.desc())
                .limit(1)
            )
            result = await db.execute(query)
            record = result.scalar_one_or_none()

            if record:
                return {
                    "id": str(record.id),
                    "from_agent": record.from_agent,
                    "to_agent": record.to_agent,
                    "handoff_type": record.handoff_type,
                    "status": record.status,
                    "rx_context": record.rx_context,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get active handoff: {e}")
            return None
