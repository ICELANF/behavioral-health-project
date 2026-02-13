"""
BehaviorOS — AgentCollaborationOrchestrator 4-Agent 协作编排器
================================================================
管理 4 款专家 Agent 之间的协作关系

拓扑:
  行为教练(上游) → 代谢/心血管(领域下游) ← 依从性(横切面)

协作场景:
  1. 新用户评估:    Coach(主导) → 领域Agent(待命) → stage≥S3 交接
  2. 代谢异常:      Metabolic(主导) + Adherence(协同) → 合并处方
  3. 运动恐惧:      Coach(前置脱敏) → Cardiac(接收) when stage→S3
  4. 多病共管:      Metabolic + Cardiac(并行) + Adherence(横切) → 处方合并
  5. 阶段回退:      领域Agent(暂停) → Coach(紧急接管) → 恢复后交还
  6. 就诊准备:      Adherence(主导) + 领域Agent(数据提供) → 就诊准备处方
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.rx_schemas import (
    ExpertAgentType,
    HandoffContext,
    HandoffRequest,
    HandoffType,
    RxContext,
    RxPrescriptionDTO,
)
from ..core.agent_handoff_service import AgentHandoffService
from ..agents.base_expert_agent import BaseExpertAgent, AgentResponse

logger = logging.getLogger(__name__)


# =====================================================================
# 协作场景枚举
# =====================================================================

class CollaborationScenario(str, Enum):
    NEW_USER_ASSESSMENT = "new_user_assessment"
    GLUCOSE_ABNORMAL = "glucose_abnormal"
    EXERCISE_FEAR = "exercise_fear"
    MULTI_MORBIDITY = "multi_morbidity"
    STAGE_REGRESSION = "stage_regression"
    PRE_VISIT = "pre_visit"
    ADHERENCE_ALERT = "adherence_alert"
    DOMAIN_COORDINATION = "domain_coordination"


# =====================================================================
# 协作决策结果
# =====================================================================

class CollaborationDecision:
    """协作编排决策结果"""

    def __init__(
        self,
        scenario: CollaborationScenario,
        primary_agent: ExpertAgentType,
        secondary_agents: List[ExpertAgentType],
        merge_strategy: str = "primary_first",
        reason: str = "",
    ):
        self.scenario = scenario
        self.primary_agent = primary_agent
        self.secondary_agents = secondary_agents
        self.merge_strategy = merge_strategy
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario.value,
            "primary_agent": self.primary_agent.value,
            "secondary_agents": [a.value for a in self.secondary_agents],
            "merge_strategy": self.merge_strategy,
            "reason": self.reason,
        }


# =====================================================================
# 合并后处方
# =====================================================================

class MergedResponse:
    """多Agent处方合并结果"""

    def __init__(
        self,
        primary: AgentResponse,
        overlays: List[AgentResponse],
        merged_message: str,
        merged_content: Dict[str, Any],
        collaboration: CollaborationDecision,
    ):
        self.primary = primary
        self.overlays = overlays
        self.merged_message = merged_message
        self.merged_content = merged_content
        self.collaboration = collaboration
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_response": self.primary.to_dict(),
            "overlay_count": len(self.overlays),
            "merged_message": self.merged_message,
            "merged_content": self.merged_content,
            "collaboration": self.collaboration.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }


# =====================================================================
# AgentCollaborationOrchestrator — 核心编排器
# =====================================================================

class AgentCollaborationOrchestrator:
    """
    4-Agent 协作编排器

    职责:
      1. 场景识别 — 根据用户上下文判断协作场景
      2. Agent 路由 — 确定主导 Agent + 辅助 Agent 列表
      3. 处方合并 — 多 Agent 处方无冲突整合
      4. 阶段回退管理 — 检测并处理阶段回退紧急事件
      5. 横切触发 — 自动触发依从性Agent横切介入

    不做:
      - 不替代 PolicyEngine 做冲突仲裁
      - 不替代各 Agent 做领域决策
      - 不直接调用 LLM (这是 MasterAgent 的职责)
    """

    def __init__(
        self,
        agents: Optional[Dict[ExpertAgentType, BaseExpertAgent]] = None,
        handoff_service: Optional[AgentHandoffService] = None,
    ):
        self._agents = agents or {}
        self._handoff_service = handoff_service or AgentHandoffService()
        logger.info(
            f"CollaborationOrchestrator initialized with "
            f"{len(self._agents)} agents"
        )

    def register_agent(self, agent: BaseExpertAgent) -> None:
        """注册专家Agent"""
        self._agents[agent.agent_type] = agent
        logger.info(f"Registered agent: {agent.agent_type.value}")

    # ---------------------------------------------------------------
    # 场景识别
    # ---------------------------------------------------------------

    def identify_scenario(
        self,
        context: RxContext,
        user_input: Dict[str, Any],
        current_agent: Optional[ExpertAgentType] = None,
    ) -> CollaborationDecision:
        """
        根据上下文识别协作场景, 返回协作决策

        决策优先级 (高→低):
          1. 阶段回退 → Coach紧急接管
          2. 安全事件 → 相关Agent暂停
          3. 多病共管 → 并行+横切
          4. 依从警报 → 依从Agent横切
          5. 新用户评估 → Coach主导
          6. 领域协作 → 正常路由
        """
        stage = context.ttm_stage
        domain = context.domain_data
        barriers = context.active_barriers

        # Priority 1: 阶段回退
        if self._detect_stage_regression(context, user_input):
            return CollaborationDecision(
                scenario=CollaborationScenario.STAGE_REGRESSION,
                primary_agent=ExpertAgentType.BEHAVIOR_COACH,
                secondary_agents=[current_agent] if current_agent else [],
                merge_strategy="coach_override",
                reason=(
                    f"Stage regression detected: "
                    f"stability={context.stage_stability:.2f}, "
                    f"efficacy={context.self_efficacy:.2f}"
                ),
            )

        # Priority 2: 依从性危机
        med_missed = domain.get("medication_missed_7d", 0)
        visit_overdue = domain.get("visit_overdue_days", 0)
        if med_missed >= 4 or visit_overdue >= 30:
            primary = current_agent or ExpertAgentType.ADHERENCE_EXPERT
            secondaries = [ExpertAgentType.ADHERENCE_EXPERT]
            if current_agent == ExpertAgentType.ADHERENCE_EXPERT:
                secondaries = []
            return CollaborationDecision(
                scenario=CollaborationScenario.ADHERENCE_ALERT,
                primary_agent=primary,
                secondary_agents=secondaries,
                merge_strategy="adherence_overlay",
                reason=(
                    f"Adherence crisis: missed={med_missed}, "
                    f"overdue={visit_overdue}d"
                ),
            )

        # Priority 3: 多病共管 (同时有代谢+心血管数据)
        has_metabolic = any(
            k in domain for k in ["glucose", "hba1c", "bmi", "weight"]
        )
        has_cardiac = any(
            k in domain for k in ["cardiac_event_type", "rehab_phase",
                                   "exercise_fear_score"]
        )
        if has_metabolic and has_cardiac:
            return CollaborationDecision(
                scenario=CollaborationScenario.MULTI_MORBIDITY,
                primary_agent=(
                    current_agent or ExpertAgentType.METABOLIC_EXPERT
                ),
                secondary_agents=[
                    ExpertAgentType.CARDIAC_EXPERT,
                    ExpertAgentType.ADHERENCE_EXPERT,
                ],
                merge_strategy="parallel_merge",
                reason="Multi-morbidity: metabolic + cardiac data present",
            )

        # Priority 4: 运动恐惧 (心血管+低阶段)
        fear_score = domain.get("exercise_fear_score", 0)
        if fear_score >= 25 and stage <= 2:
            return CollaborationDecision(
                scenario=CollaborationScenario.EXERCISE_FEAR,
                primary_agent=ExpertAgentType.BEHAVIOR_COACH,
                secondary_agents=[ExpertAgentType.CARDIAC_EXPERT],
                merge_strategy="coach_first_then_handoff",
                reason=f"Exercise fear={fear_score} + stage=S{stage} → Coach first",
            )

        # Priority 5: 就诊准备
        next_visit_days = domain.get("next_visit_in_days", 999)
        if next_visit_days <= 3:
            return CollaborationDecision(
                scenario=CollaborationScenario.PRE_VISIT,
                primary_agent=ExpertAgentType.ADHERENCE_EXPERT,
                secondary_agents=[
                    a for a in [
                        ExpertAgentType.METABOLIC_EXPERT,
                        ExpertAgentType.CARDIAC_EXPERT,
                    ]
                    if a != current_agent
                ],
                merge_strategy="adherence_lead",
                reason=f"Pre-visit: {next_visit_days}d until appointment",
            )

        # Priority 6: 新用户低阶段
        if stage <= 2 and not current_agent:
            return CollaborationDecision(
                scenario=CollaborationScenario.NEW_USER_ASSESSMENT,
                primary_agent=ExpertAgentType.BEHAVIOR_COACH,
                secondary_agents=[],
                merge_strategy="single_agent",
                reason=f"New/low-stage user: S{stage}",
            )

        # Default: 当前Agent单独处理
        return CollaborationDecision(
            scenario=CollaborationScenario.DOMAIN_COORDINATION,
            primary_agent=current_agent or ExpertAgentType.BEHAVIOR_COACH,
            secondary_agents=self._detect_crosscut_needs(context, domain),
            merge_strategy="primary_first",
            reason="Standard domain processing",
        )

    # ---------------------------------------------------------------
    # 编排执行
    # ---------------------------------------------------------------

    async def orchestrate(
        self,
        user_input: Dict[str, Any],
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        current_agent: Optional[ExpertAgentType] = None,
        db=None,
    ) -> MergedResponse:
        """
        编排多Agent协作并返回合并结果

        流程:
          1. 构建上下文 → 场景识别
          2. 调用主Agent
          3. 调用辅助Agent(如有)
          4. 合并处方和消息
        """
        # Step 1: 上下文 & 场景识别
        profile = user_input.get("behavioral_profile", {})
        from ..core.rx_schemas import BigFiveProfile
        context = RxContext(
            user_id=user_id,
            session_id=session_id,
            ttm_stage=profile.get("ttm_stage", 0),
            stage_readiness=profile.get("stage_readiness", 0.5),
            stage_stability=profile.get("stage_stability", 0.5),
            personality=BigFiveProfile(**profile.get("bigfive", {})),
            capacity_score=profile.get("capacity_score", 0.5),
            self_efficacy=profile.get("self_efficacy", 0.5),
            domain_data={
                **user_input.get("device_data", {}),
                **user_input.get("domain_data", {}),
            },
            active_barriers=profile.get("active_barriers", []),
            recent_adherence=profile.get("recent_adherence", 0.5),
            risk_level=profile.get("risk_level", "normal"),
        )

        decision = self.identify_scenario(context, user_input, current_agent)
        logger.info(
            f"Collaboration scenario: {decision.scenario.value} "
            f"primary={decision.primary_agent.value} "
            f"secondaries={[a.value for a in decision.secondary_agents]}"
        )

        # Step 2: 调用主Agent
        primary_agent = self._agents.get(decision.primary_agent)
        if not primary_agent:
            raise ValueError(
                f"Primary agent {decision.primary_agent.value} not registered"
            )
        primary_response = await primary_agent.process(
            user_input, user_id, session_id, db
        )

        # Step 3: 调用辅助Agent
        overlay_responses = []
        for agent_type in decision.secondary_agents:
            agent = self._agents.get(agent_type)
            if agent:
                try:
                    overlay = await agent.process(
                        user_input, user_id, session_id, db
                    )
                    overlay_responses.append(overlay)
                except Exception as e:
                    logger.warning(
                        f"Secondary agent {agent_type.value} failed: {e}"
                    )

        # Step 4: 合并
        merged_msg, merged_content = self._merge_responses(
            primary_response, overlay_responses, decision
        )

        return MergedResponse(
            primary=primary_response,
            overlays=overlay_responses,
            merged_message=merged_msg,
            merged_content=merged_content,
            collaboration=decision,
        )

    # ---------------------------------------------------------------
    # 阶段回退检测
    # ---------------------------------------------------------------

    def _detect_stage_regression(
        self, context: RxContext, user_input: Dict[str, Any]
    ) -> bool:
        """
        检测阶段回退信号

        触发条件 (满足任一):
          - 阶段稳定度 < 0.3
          - 自我效能急剧下降 (< 0.2)
          - 用户文本含放弃意向
        """
        if context.stage_stability < 0.3:
            return True
        if context.self_efficacy < 0.2 and context.ttm_stage >= 3:
            return True

        message = user_input.get("message", "").lower()
        regression_signals = [
            "不想做了", "放弃", "没用", "做不到", "太难了",
            "give up", "quit", "can't do", "impossible",
            "算了", "不行了", "坚持不下去",
        ]
        return any(s in message for s in regression_signals)

    # ---------------------------------------------------------------
    # 横切需求检测
    # ---------------------------------------------------------------

    def _detect_crosscut_needs(
        self,
        context: RxContext,
        domain: Dict[str, Any],
    ) -> List[ExpertAgentType]:
        """检测是否需要依从性Agent横切介入"""
        crosscuts = []
        med_missed = domain.get("medication_missed_7d", 0)
        visit_overdue = domain.get("visit_overdue_days", 0)

        if med_missed >= 2 or visit_overdue >= 7:
            crosscuts.append(ExpertAgentType.ADHERENCE_EXPERT)

        return crosscuts

    # ---------------------------------------------------------------
    # 处方合并
    # ---------------------------------------------------------------

    def _merge_responses(
        self,
        primary: AgentResponse,
        overlays: List[AgentResponse],
        decision: CollaborationDecision,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        合并多Agent响应

        合并策略:
          single_agent     — 直接返回主Agent
          primary_first    — 主Agent消息 + 辅助Agent内容追加
          adherence_overlay — 主Agent消息 + 依从性提醒追加
          coach_override   — Coach消息覆盖领域Agent
          parallel_merge   — 并行领域内容合并
          adherence_lead   — 依从Agent主导, 领域Agent数据汇入
        """
        strategy = decision.merge_strategy

        if not overlays or strategy == "single_agent":
            return primary.user_message, primary.domain_content

        if strategy == "coach_override":
            merged_content = {
                "coach": primary.domain_content,
                "suspended_domains": [
                    {
                        "agent": o.agent_type.value,
                        "status": "paused_for_regression",
                    }
                    for o in overlays
                ],
            }
            return primary.user_message, merged_content

        if strategy == "adherence_overlay":
            adherence_notes = []
            for o in overlays:
                if o.agent_type == ExpertAgentType.ADHERENCE_EXPERT:
                    adherence_notes.append(o.user_message)

            merged_msg = primary.user_message
            if adherence_notes:
                merged_msg += "\n\n---\n📋 " + "\n".join(adherence_notes)

            merged_content = {
                "primary": primary.domain_content,
                "adherence_overlay": [o.domain_content for o in overlays],
            }
            return merged_msg, merged_content

        if strategy == "parallel_merge":
            merged_msg = primary.user_message
            for o in overlays:
                if o.user_message and o.agent_type != primary.agent_type:
                    # 仅追加非重复的关键提醒
                    short_note = o.user_message.split("\n")[0]
                    merged_msg += f"\n\n💡 {short_note}"

            merged_content = {
                "primary": {
                    "agent": primary.agent_type.value,
                    "content": primary.domain_content,
                },
                "parallel": [
                    {
                        "agent": o.agent_type.value,
                        "content": o.domain_content,
                    }
                    for o in overlays
                ],
            }
            return merged_msg, merged_content

        # Default: primary_first / adherence_lead
        merged_content = {
            "primary": primary.domain_content,
            "supplements": [o.domain_content for o in overlays],
        }
        merged_msg = primary.user_message
        return merged_msg, merged_content

    # ---------------------------------------------------------------
    # Agent 注册验证
    # ---------------------------------------------------------------

    def get_registered_agents(self) -> List[str]:
        """返回已注册的Agent列表"""
        return [a.value for a in self._agents.keys()]

    def is_fully_operational(self) -> bool:
        """检查4款Agent是否全部注册"""
        required = {
            ExpertAgentType.BEHAVIOR_COACH,
            ExpertAgentType.METABOLIC_EXPERT,
            ExpertAgentType.CARDIAC_EXPERT,
            ExpertAgentType.ADHERENCE_EXPERT,
        }
        return required.issubset(self._agents.keys())
