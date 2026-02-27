"""
BehaviorOS — MasterAgent 专家Agent集成补丁
============================================
本文件展示如何将 4 款专家Agent 接入 v31 MasterAgent 9步流程

集成点:
  Step 4:   Agent Router — 新增专家Agent路由判断
  Step 5-6: Agent调用 — 通过 CollaborationOrchestrator 编排
  Step 7:   Intervention — 使用 RxPrescription 替代通用干预

不修改 MasterAgent 核心流程, 通过钩子/策略模式注入。

使用方式:
  在 v31 main.py 启动时调用:
    from behavior_rx.patches.master_agent_integration import (
        setup_expert_agents,
        ExpertAgentRouter,
    )
    expert_router = setup_expert_agents()
    # 注入到 MasterAgent
    master_agent.register_expert_router(expert_router)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ..core.rx_schemas import ExpertAgentType, RxContext
from ..core.behavior_rx_engine import BehaviorRxEngine
from ..core.agent_handoff_service import AgentHandoffService
from ..core.agent_collaboration_orchestrator import (
    AgentCollaborationOrchestrator,
    CollaborationDecision,
    MergedResponse,
)
from ..core.rx_conflict_resolver import RxConflictResolver
from ..agents.behavior_coach_agent import BehaviorCoachAgent
from ..agents.metabolic_expert_agent import MetabolicExpertAgent
from ..agents.cardiac_expert_agent import CardiacExpertAgent
from ..agents.adherence_expert_agent import AdherenceExpertAgent

logger = logging.getLogger(__name__)


# =====================================================================
# 专家Agent路由器
# =====================================================================

class ExpertAgentRouter:
    """
    专家Agent路由器 — 在 MasterAgent Step 4 注入

    判断逻辑:
      1. 用户是否有专家Agent匹配的领域数据?
      2. 用户当前TTM阶段是否适合专家Agent?
      3. 是否存在进行中的专家Agent会话?

    如果命中专家Agent, 则绕过通用Agent路由,
    直接走 CollaborationOrchestrator 编排流程。
    """

    def __init__(
        self,
        orchestrator: AgentCollaborationOrchestrator,
    ):
        self._orchestrator = orchestrator

        # 领域关键词 → Agent 映射
        self._domain_keywords = {
            ExpertAgentType.METABOLIC_EXPERT: [
                "血糖", "糖尿病", "胰岛素", "代谢", "HbA1c", "glucose",
                "体重", "BMI", "减重", "饮食", "营养",
            ],
            ExpertAgentType.CARDIAC_EXPERT: [
                "心脏", "心血管", "康复", "运动处方", "心率", "胸痛",
                "支架", "搭桥", "心梗", "心衰", "血压",
            ],
            ExpertAgentType.ADHERENCE_EXPERT: [
                "服药", "吃药", "忘记吃药", "漏服", "复查", "检查",
                "医嘱", "依从", "不想吃药", "药太多",
            ],
            ExpertAgentType.BEHAVIOR_COACH: [
                "不想改变", "没动力", "害怕", "做不到", "为什么要",
                "有什么用", "放弃", "坚持不下去",
            ],
        }

        # 领域数据键 → Agent 映射
        self._domain_data_keys = {
            ExpertAgentType.METABOLIC_EXPERT: [
                "glucose", "hba1c", "bmi", "weight", "fasting_glucose",
            ],
            ExpertAgentType.CARDIAC_EXPERT: [
                "cardiac_event_type", "rehab_phase", "exercise_fear_score",
                "resting_hr", "exercise_hr",
            ],
            ExpertAgentType.ADHERENCE_EXPERT: [
                "medication_missed_7d", "visit_overdue_days", "mmas_score",
                "medications", "pending_tests",
            ],
        }

    def should_route_to_expert(
        self,
        user_input: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> Tuple[bool, Optional[ExpertAgentType]]:
        """
        判断是否应路由到专家Agent

        Returns:
            (should_route, suggested_agent)
        """
        message = user_input.get("message", "").lower()
        domain_data = {
            **user_input.get("device_data", {}),
            **user_input.get("domain_data", {}),
        }
        ttm_stage = user_profile.get("ttm_stage", 0)

        # 1. 文本关键词匹配
        matched_agent = self._match_by_keywords(message)

        # 2. 领域数据匹配
        if not matched_agent:
            matched_agent = self._match_by_domain_data(domain_data)

        # 3. 低阶段用户 → Coach
        if not matched_agent and ttm_stage <= 2:
            matched_agent = ExpertAgentType.BEHAVIOR_COACH

        if matched_agent:
            logger.info(
                f"Expert routing: {matched_agent.value} "
                f"(stage=S{ttm_stage})"
            )
            return True, matched_agent

        return False, None

    def _match_by_keywords(self, text: str) -> Optional[ExpertAgentType]:
        """文本关键词匹配"""
        scores = {}
        for agent_type, keywords in self._domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[agent_type] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    def _match_by_domain_data(
        self, domain_data: Dict[str, Any]
    ) -> Optional[ExpertAgentType]:
        """领域数据键匹配"""
        scores = {}
        for agent_type, keys in self._domain_data_keys.items():
            score = sum(1 for k in keys if k in domain_data)
            if score > 0:
                scores[agent_type] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    async def route_and_execute(
        self,
        user_input: Dict[str, Any],
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        current_agent: Optional[ExpertAgentType] = None,
        db=None,
    ) -> MergedResponse:
        """路由到专家Agent并执行协作编排"""
        return await self._orchestrator.orchestrate(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            current_agent=current_agent,
            db=db,
        )


# =====================================================================
# 初始化函数 — 在 v31 启动时调用
# =====================================================================

def setup_expert_agents(
    rx_engine: Optional[BehaviorRxEngine] = None,
    handoff_service: Optional[AgentHandoffService] = None,
) -> ExpertAgentRouter:
    """
    初始化并注册所有专家Agent

    使用方式 (v31 main.py):
        from behavior_rx.patches.master_agent_integration import setup_expert_agents
        expert_router = setup_expert_agents()
        app.state.expert_router = expert_router

    Returns:
        ExpertAgentRouter — 注入到 MasterAgent 的专家路由器
    """
    engine = rx_engine or BehaviorRxEngine()
    handoff = handoff_service or AgentHandoffService()

    # 实例化 4 款 Agent
    coach = BehaviorCoachAgent(rx_engine=engine, handoff_service=handoff)
    metabolic = MetabolicExpertAgent(rx_engine=engine, handoff_service=handoff)
    cardiac = CardiacExpertAgent(rx_engine=engine, handoff_service=handoff)
    adherence = AdherenceExpertAgent(rx_engine=engine, handoff_service=handoff)

    # 注册到编排器
    orchestrator = AgentCollaborationOrchestrator(
        handoff_service=handoff,
    )
    orchestrator.register_agent(coach)
    orchestrator.register_agent(metabolic)
    orchestrator.register_agent(cardiac)
    orchestrator.register_agent(adherence)

    logger.info(
        f"Expert agents initialized: "
        f"{orchestrator.get_registered_agents()}"
    )
    assert orchestrator.is_fully_operational(), "Not all agents registered!"

    return ExpertAgentRouter(orchestrator=orchestrator)


# =====================================================================
# MasterAgent 集成钩子示例
# =====================================================================

def patch_master_agent_v0(master_agent_class):
    """
    为 MasterAgent 添加专家Agent处理分支

    在 Step 4 (Agent Router) 之后插入专家Agent判断:
      如果命中专家Agent → 走 CollaborationOrchestrator
      否则 → 走原始 12 Agent 路由

    使用方式:
        from core.master_agent_v0 import MasterAgentV0
        from behavior_rx.patches.master_agent_integration import (
            patch_master_agent_v0
        )
        patch_master_agent_v0(MasterAgentV0)
    """
    original_process = master_agent_class.process

    async def patched_process(self, user_input, user_id, session_id=None, db=None):
        """增强版 MasterAgent process — 支持专家Agent路由"""

        # 检查是否有专家路由器
        expert_router = getattr(self, '_expert_router', None)
        if expert_router is None:
            return await original_process(
                self, user_input, user_id, session_id, db
            )

        # 专家Agent路由判断
        profile = user_input.get("behavioral_profile", {})
        should_route, suggested_agent = expert_router.should_route_to_expert(
            user_input, profile
        )

        if should_route:
            logger.info(
                f"MasterAgent: routing to expert {suggested_agent.value}"
            )
            merged = await expert_router.route_and_execute(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                current_agent=suggested_agent,
                db=db,
            )
            # 转换为 MasterAgent 标准响应格式
            return {
                "response": merged.merged_message,
                "agent_type": "expert",
                "expert_agent": merged.collaboration.primary_agent.value,
                "collaboration_scenario": merged.collaboration.scenario.value,
                "domain_content": merged.merged_content,
                "rx": merged.primary.rx.model_dump()
                if merged.primary.rx else None,
            }

        # 回退到原始处理流程
        return await original_process(
            self, user_input, user_id, session_id, db
        )

    # 注入方法
    master_agent_class.process = patched_process

    # 添加注册方法
    def register_expert_router(self, router: ExpertAgentRouter):
        self._expert_router = router
        logger.info("Expert router registered to MasterAgent")

    master_agent_class.register_expert_router = register_expert_router

    logger.info("MasterAgent patched with expert agent routing")
