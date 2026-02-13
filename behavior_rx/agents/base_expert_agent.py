"""
BehaviorOS — BaseExpertAgent 专家Agent抽象基类
===============================================
所有 4 款 Expert Agent 的共同父类

核心流程 (Template Method):
  1. receive_input()     — 接收用户输入 + 设备数据
  2. assess_context()    — 构建 RxContext (调用 BAPS)
  3. compute_rx()        — 调用 BehaviorRxEngine 生成处方
  4. apply_domain()      — 【子类实现】领域专业包装
  5. check_handoff()     — 检查是否需要交接
  6. format_response()   — 组装最终响应 (处方隐藏在专业内容之下)
  7. persist_trace()     — 决策追踪记录

设计原则:
  - 行为处方是隐藏基座, 用户看到的是领域专业内容
  - 每个子类只需实现 apply_domain() 和 _get_expert_rules()
  - 交接检测自动运行
"""

from __future__ import annotations

import abc
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..core.behavior_rx_engine import BehaviorRxEngine
from ..core.agent_handoff_service import AgentHandoffService
from ..core.rx_schemas import (
    BigFiveProfile,
    CommunicationStyle,
    ExpertAgentType,
    HandoffContext,
    HandoffRequest,
    HandoffType,
    RxContext,
    RxIntensity,
    RxPrescriptionDTO,
    RxStrategyType,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 专家规则定义
# =====================================================================

class ExpertRule:
    """
    专家决策规则

    每个 Expert Agent 持有一组规则, 根据条件触发特定动作。
    规则在 apply_domain() 流程中被评估。
    """

    def __init__(
        self,
        rule_id: str,
        name: str,
        condition: str,
        action: str,
        priority: int = 5,
        bind_dimension: str = "",
        description: str = "",
    ):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition  # Python 表达式字符串 (简化版)
        self.action = action        # 动作标识符
        self.priority = priority
        self.bind_dimension = bind_dimension
        self.description = description

    def evaluate(self, facts: Dict[str, Any]) -> bool:
        """
        评估规则条件

        Args:
            facts: 事实字典 (由子类构建)

        Returns:
            True if 条件满足
        """
        try:
            return bool(eval(self.condition, {"__builtins__": {}}, facts))
        except Exception:
            return False


# =====================================================================
# Agent 响应结构
# =====================================================================

class AgentResponse:
    """Agent 统一响应结构"""

    def __init__(
        self,
        agent_type: ExpertAgentType,
        rx: RxPrescriptionDTO,
        domain_content: Dict[str, Any],
        user_message: str,
        handoff_needed: bool = False,
        handoff_target: Optional[ExpertAgentType] = None,
        handoff_type: Optional[HandoffType] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.agent_type = agent_type
        self.rx = rx
        self.domain_content = domain_content
        self.user_message = user_message
        self.handoff_needed = handoff_needed
        self.handoff_target = handoff_target
        self.handoff_type = handoff_type
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type.value,
            "user_message": self.user_message,
            "domain_content": self.domain_content,
            "rx_summary": {
                "strategy": self.rx.strategy_type.value,
                "intensity": self.rx.intensity.value,
                "communication_style": self.rx.communication_style.value,
                "goal": self.rx.goal_behavior,
            },
            "handoff": {
                "needed": self.handoff_needed,
                "target": self.handoff_target.value if self.handoff_target else None,
                "type": self.handoff_type.value if self.handoff_type else None,
            },
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


# =====================================================================
# BaseExpertAgent — 抽象基类
# =====================================================================

class BaseExpertAgent(abc.ABC):
    """
    专家 Agent 抽象基类

    子类必须实现:
      - agent_type (property) → ExpertAgentType
      - apply_domain(rx, context, user_input) → domain_content, user_message
      - _get_expert_rules() → List[ExpertRule]
      - _build_domain_facts(context, user_input) → Dict[str, Any]
    """

    def __init__(
        self,
        rx_engine: Optional[BehaviorRxEngine] = None,
        handoff_service: Optional[AgentHandoffService] = None,
    ):
        self._rx_engine = rx_engine or BehaviorRxEngine()
        self._handoff_service = handoff_service or AgentHandoffService()
        self._expert_rules = self._get_expert_rules()
        logger.info(
            f"{self.__class__.__name__} initialized with "
            f"{len(self._expert_rules)} expert rules"
        )

    # ---------------------------------------------------------------
    # 抽象属性和方法 (子类必须实现)
    # ---------------------------------------------------------------

    @property
    @abc.abstractmethod
    def agent_type(self) -> ExpertAgentType:
        """Agent 类型标识"""
        ...

    @abc.abstractmethod
    def apply_domain(
        self,
        rx: RxPrescriptionDTO,
        context: RxContext,
        user_input: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """
        领域专业包装 — 将行为处方转化为领域专业内容

        这是「冰山模型」的关键:
          - 输入: RxPrescription (水面下)
          - 输出: 领域专业内容 (水面上) + 用户消息

        Args:
            rx: 行为处方
            context: 三维上下文
            user_input: 用户原始输入

        Returns:
            (domain_content_dict, user_facing_message)
        """
        ...

    @abc.abstractmethod
    def _get_expert_rules(self) -> List[ExpertRule]:
        """返回该 Agent 的专家规则集"""
        ...

    @abc.abstractmethod
    def _build_domain_facts(
        self, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建领域事实字典 (用于规则评估)"""
        ...

    # ---------------------------------------------------------------
    # 模板方法: process — Agent 主处理流程
    # ---------------------------------------------------------------

    async def process(
        self,
        user_input: Dict[str, Any],
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        db=None,
    ) -> AgentResponse:
        """
        Agent 主处理流程 (Template Method)

        流程:
          1. assess_context — 构建三维上下文
          2. evaluate_rules — 评估专家规则
          3. compute_rx     — 生成行为处方
          4. apply_domain   — 领域专业包装
          5. check_handoff  — 交接检测
          6. 组装响应

        Args:
            user_input: {
                "message": str,
                "device_data": dict,
                "behavioral_profile": dict,  # BAPS 数据
                "domain_data": dict,         # 领域特定数据
            }
            user_id: 用户 ID
            session_id: 会话 ID
            db: 数据库会话

        Returns:
            AgentResponse
        """
        # Step 1: 构建三维上下文
        context = self._assess_context(user_input, user_id, session_id)
        logger.info(
            f"{self.agent_type.value} processing: "
            f"user={user_id} stage=S{context.ttm_stage}"
        )

        # Step 2: 评估专家规则
        domain_facts = self._build_domain_facts(context, user_input)
        triggered_rules = self._evaluate_rules(domain_facts)

        # Step 3: 确定策略覆盖 (规则可能强制指定策略)
        override_strategy = None
        override_intensity = None
        for rule in triggered_rules:
            if rule.action.startswith("force_strategy:"):
                strategy_name = rule.action.split(":")[1]
                try:
                    override_strategy = RxStrategyType(strategy_name)
                except ValueError:
                    pass
            elif rule.action.startswith("force_intensity:"):
                intensity_name = rule.action.split(":")[1]
                try:
                    override_intensity = RxIntensity(intensity_name)
                except ValueError:
                    pass

        # Step 4: 生成行为处方
        rx = await self._rx_engine.compute_rx_async(
            context=context,
            agent_type=self.agent_type,
            db=db,
            persist=db is not None,
            override_strategy=override_strategy,
            override_intensity=override_intensity,
        )

        # Step 5: 领域专业包装
        domain_content, user_message = self.apply_domain(rx, context, user_input)

        # Step 6: 交接检测
        handoff_context = HandoffContext(
            stage=context.ttm_stage,
            readiness=context.stage_readiness,
            personality_profile=context.personality,
            capacity_score=context.capacity_score,
            active_rx_id=rx.rx_id,
            domain_state={
                "self_efficacy": context.self_efficacy,
                "stage_stability": context.stage_stability,
                **context.domain_data,
            },
        )
        metrics = self._extract_handoff_metrics(user_input, context)
        should_handoff, handoff_type, target = self._handoff_service.check_handoff_needed(
            current_agent=self.agent_type,
            context=handoff_context,
            current_rx=rx,
            metrics=metrics,
        )

        # Step 7: 如果需要交接, 发起交接
        if should_handoff and target:
            handoff_req = HandoffRequest(
                user_id=user_id,
                session_id=session_id,
                from_agent=self.agent_type,
                to_agent=target,
                handoff_type=handoff_type,
                trigger_reason=f"Auto-detected by {self.agent_type.value}",
                rx_context=handoff_context,
                rx_prescription_id=rx.rx_id,
            )
            await self._handoff_service.initiate_handoff(handoff_req, db)

        # Step 8: 组装响应
        response = AgentResponse(
            agent_type=self.agent_type,
            rx=rx,
            domain_content=domain_content,
            user_message=user_message,
            handoff_needed=should_handoff,
            handoff_target=target,
            handoff_type=handoff_type,
            metadata={
                "triggered_rules": [r.rule_id for r in triggered_rules],
                "rx_confidence": rx.confidence,
                "rx_reasoning": rx.reasoning,
            },
        )

        return response

    # ---------------------------------------------------------------
    # 上下文构建
    # ---------------------------------------------------------------

    def _assess_context(
        self,
        user_input: Dict[str, Any],
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID],
    ) -> RxContext:
        """
        从用户输入构建三维上下文

        数据来源:
          - behavioral_profile → TTM 阶段, BigFive, CAPACITY
          - device_data → 领域特定数据
          - message → 障碍检测
        """
        profile = user_input.get("behavioral_profile", {})
        device_data = user_input.get("device_data", {})
        domain_data = user_input.get("domain_data", {})

        # BigFive
        bigfive_raw = profile.get("bigfive", {})
        personality = BigFiveProfile(
            O=bigfive_raw.get("O", 50),
            C=bigfive_raw.get("C", 50),
            E=bigfive_raw.get("E", 50),
            A=bigfive_raw.get("A", 50),
            N=bigfive_raw.get("N", 50),
        )

        # 障碍检测
        barriers = profile.get("active_barriers", [])
        message = user_input.get("message", "")
        barriers.extend(self._detect_barriers_from_text(message))

        return RxContext(
            user_id=user_id,
            session_id=session_id,
            ttm_stage=profile.get("ttm_stage", 0),
            stage_readiness=profile.get("stage_readiness", 0.5),
            stage_stability=profile.get("stage_stability", 0.5),
            personality=personality,
            capacity_score=profile.get("capacity_score", 0.5),
            self_efficacy=profile.get("self_efficacy", 0.5),
            domain_data={**device_data, **domain_data},
            active_barriers=barriers,
            recent_adherence=profile.get("recent_adherence", 0.5),
            risk_level=profile.get("risk_level", "normal"),
        )

    def _detect_barriers_from_text(self, text: str) -> List[str]:
        """从用户文本中检测障碍类型"""
        barriers = []
        barrier_keywords = {
            "fear": ["害怕", "恐惧", "担心", "不敢", "危险", "scared", "afraid"],
            "forgetfulness": ["忘了", "忘记", "记不住", "forgot", "forget"],
            "low_motivation": ["没动力", "不想", "没意思", "懒得", "算了"],
            "cognitive": ["不懂", "不理解", "不明白", "为什么", "怎么回事"],
            "economic": ["太贵", "买不起", "费用", "expensive"],
        }
        text_lower = text.lower()
        for barrier, keywords in barrier_keywords.items():
            if any(kw in text_lower for kw in keywords):
                barriers.append(barrier)
        return barriers

    # ---------------------------------------------------------------
    # 规则评估
    # ---------------------------------------------------------------

    def _evaluate_rules(self, facts: Dict[str, Any]) -> List[ExpertRule]:
        """评估所有专家规则, 返回触发的规则 (按优先级排序)"""
        triggered = []
        for rule in self._expert_rules:
            if rule.evaluate(facts):
                triggered.append(rule)
                logger.debug(f"Rule triggered: {rule.rule_id} - {rule.name}")
        triggered.sort(key=lambda r: r.priority, reverse=True)
        return triggered

    # ---------------------------------------------------------------
    # 交接指标提取
    # ---------------------------------------------------------------

    def _extract_handoff_metrics(
        self, user_input: Dict[str, Any], context: RxContext
    ) -> Dict[str, Any]:
        """提取交接检测所需的指标 (子类可覆盖扩展)"""
        domain_data = user_input.get("domain_data", {})
        return {
            "medication_missed_7d": domain_data.get("medication_missed_7d", 0),
            "visit_overdue_days": domain_data.get("visit_overdue_days", 0),
            "overall_adherence": context.recent_adherence,
            "comorbidity": domain_data.get("comorbidity", []),
        }

    # ---------------------------------------------------------------
    # 沟通风格适配
    # ---------------------------------------------------------------

    def adapt_message_style(
        self,
        message: str,
        style: CommunicationStyle,
    ) -> str:
        """
        根据沟通风格适配消息语气

        这是一个简化实现 — 实际场景中由 LLM 完成风格适配
        此处提供风格指令前缀
        """
        style_prefixes = {
            CommunicationStyle.EMPATHETIC:
                "[语气: 温暖共情, 认可感受, 不施加压力] ",
            CommunicationStyle.DATA_DRIVEN:
                "[语气: 客观专业, 提供数据, 逻辑清晰] ",
            CommunicationStyle.EXPLORATORY:
                "[语气: 开放探索, 提问引导, 启发思考] ",
            CommunicationStyle.SOCIAL_PROOF:
                "[语气: 同伴经验, 社区归属, 榜样激励] ",
            CommunicationStyle.CHALLENGE:
                "[语气: 积极挑战, 设立目标, 激发竞争心] ",
            CommunicationStyle.NEUTRAL:
                "[语气: 中性专业, 清晰简洁] ",
        }
        prefix = style_prefixes.get(style, "")
        return f"{prefix}{message}"
