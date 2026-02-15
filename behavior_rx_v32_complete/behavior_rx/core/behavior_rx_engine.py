"""
BehaviorOS — BehaviorRxEngine 行为处方核心引擎
===============================================
所有 Expert Agent 的共享基座服务 (非Agent, 是Service)

核心方法:
  compute_rx(context, agent_type) → RxPrescriptionDTO

三维计算:
  1. TTM 阶段 (S0-S6) → 策略类型 + 强度
  2. BigFive 人格     → 沟通风格 + 策略微调
  3. CAPACITY 能力    → 难度校准 + 节奏

设计原则:
  - 纯函数式计算, 无副作用
  - 每次调用生成完整 RxPrescription 对象
  - 上层 Agent 拿到处方后进行领域包装
  - <200ms P99 延迟要求
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .rx_schemas import (
    BigFiveProfile,
    CommunicationStyle,
    EscalationRule,
    ExpertAgentType,
    MicroAction,
    RewardTrigger,
    RxContext,
    RxIntensity,
    RxPrescriptionDTO,
    RxStrategyType,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 策略选择矩阵: TTM 阶段 → 推荐策略 (优先级排序)
# =====================================================================

STAGE_STRATEGY_MATRIX: Dict[int, List[RxStrategyType]] = {
    0: [  # 前意识 — 认知激活
        RxStrategyType.CONSCIOUSNESS_RAISING,
        RxStrategyType.DRAMATIC_RELIEF,
    ],
    1: [  # 意识 — 认知深化 + 情感链接
        RxStrategyType.CONSCIOUSNESS_RAISING,
        RxStrategyType.SELF_REEVALUATION,
        RxStrategyType.DRAMATIC_RELIEF,
        RxStrategyType.DECISIONAL_BALANCE,
    ],
    2: [  # 准备 — 决策 + 承诺
        RxStrategyType.DECISIONAL_BALANCE,
        RxStrategyType.SELF_LIBERATION,
        RxStrategyType.SELF_REEVALUATION,
        RxStrategyType.COGNITIVE_RESTRUCTURING,
        RxStrategyType.SELF_MONITORING,
    ],
    3: [  # 行动 — 行为执行
        RxStrategyType.STIMULUS_CONTROL,
        RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.HABIT_STACKING,
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.COGNITIVE_RESTRUCTURING,
        RxStrategyType.RELAPSE_PREVENTION,
    ],
    4: [  # 维持 — 巩固防复发
        RxStrategyType.RELAPSE_PREVENTION,
        RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.STIMULUS_CONTROL,
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.HABIT_STACKING,
    ],
    5: [  # 巩固 — 自主化
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.RELAPSE_PREVENTION,
        RxStrategyType.CONTINGENCY_MANAGEMENT,
    ],
    6: [  # 终止 — 监测
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.RELAPSE_PREVENTION,
    ],
}

# =====================================================================
# 强度决策矩阵: TTM 阶段 × CAPACITY → 强度
# =====================================================================

INTENSITY_MATRIX: Dict[int, Dict[str, RxIntensity]] = {
    0: {"low": RxIntensity.MINIMAL,  "mid": RxIntensity.MINIMAL,  "high": RxIntensity.LOW},
    1: {"low": RxIntensity.MINIMAL,  "mid": RxIntensity.LOW,      "high": RxIntensity.LOW},
    2: {"low": RxIntensity.LOW,      "mid": RxIntensity.MODERATE,  "high": RxIntensity.MODERATE},
    3: {"low": RxIntensity.MODERATE, "mid": RxIntensity.MODERATE,  "high": RxIntensity.HIGH},
    4: {"low": RxIntensity.MODERATE, "mid": RxIntensity.HIGH,      "high": RxIntensity.HIGH},
    5: {"low": RxIntensity.LOW,      "mid": RxIntensity.MODERATE,  "high": RxIntensity.MODERATE},
    6: {"low": RxIntensity.MINIMAL,  "mid": RxIntensity.LOW,      "high": RxIntensity.LOW},
}


# =====================================================================
# 人格 → 沟通风格映射
# =====================================================================

def _determine_communication_style(personality: BigFiveProfile) -> CommunicationStyle:
    """
    根据 BigFive 人格剖面确定最优沟通风格

    规则优先级:
      1. 高N(≥65) → 共情温暖 (最高优先: 情绪稳定性差的人需要安全感)
      2. 高C(≥65) → 数据驱动
      3. 高E(≥65) → 挑战激励
      4. 高A(≥65) → 社会认同
      5. 高O(≥65) → 探索引导
      6. 以上都不突出 → 中性专业
    """
    if personality.is_high("N"):
        return CommunicationStyle.EMPATHETIC
    if personality.is_high("C"):
        return CommunicationStyle.DATA_DRIVEN
    if personality.is_high("E"):
        return CommunicationStyle.CHALLENGE
    if personality.is_high("A"):
        return CommunicationStyle.SOCIAL_PROOF
    if personality.is_high("O"):
        return CommunicationStyle.EXPLORATORY
    return CommunicationStyle.NEUTRAL


# =====================================================================
# 节奏决策
# =====================================================================

def _determine_pace(
    stage: int,
    capacity: float,
    stability: float,
    personality: BigFiveProfile,
) -> str:
    """
    确定推进节奏

    规则:
      - 低阶段 (S0-S1) 或 低能力 (<0.3) → slow
      - 高阶段 (S4+) 或 高能力 (>0.7) 且 稳定 (>0.6) → fast
      - 高N 且 低稳定性 → slow (安全优先)
      - 其他 → standard
    """
    if stage <= 1 or capacity < 0.3:
        return "slow"
    if personality.is_high("N") and stability < 0.4:
        return "slow"
    if stage >= 4 and capacity > 0.7 and stability > 0.6:
        return "fast"
    return "standard"


# =====================================================================
# 阻力阈值计算
# =====================================================================

def _calculate_resistance_threshold(
    personality: BigFiveProfile,
    capacity: float,
    stage: int,
) -> float:
    """
    计算阻力切换阈值

    高N/低C → 更低阈值 (更敏感的策略切换)
    高C/高能力 → 更高阈值 (更多耐心)
    低阶段 → 更低阈值
    """
    base = 0.3

    # 人格调节
    if personality.is_high("N"):
        base -= 0.08  # 高神经质 → 早切换
    if personality.is_high("C"):
        base += 0.05  # 高尽责性 → 多坚持
    if personality.is_low("C"):
        base -= 0.05  # 低尽责性 → 早切换

    # 能力调节
    base += (capacity - 0.5) * 0.1

    # 阶段调节
    if stage <= 1:
        base -= 0.05  # 低阶段更敏感

    return max(0.15, min(0.5, base))


# =====================================================================
# 升级规则生成
# =====================================================================

def _generate_escalation_rules(
    agent_type: ExpertAgentType,
    stage: int,
    personality: BigFiveProfile,
) -> List[EscalationRule]:
    """生成默认升级规则"""
    rules = []

    # 通用: 阻力超标 → 切换策略
    rules.append(EscalationRule(
        condition="resistance_score > resistance_threshold for 3 consecutive sessions",
        action="switch_strategy",
        priority=5,
    ))

    # 通用: 阶段回退 → 交接教练
    if agent_type != ExpertAgentType.BEHAVIOR_COACH:
        rules.append(EscalationRule(
            condition="ttm_stage decreased by ≥2 stages",
            action="handoff",
            target_agent=ExpertAgentType.BEHAVIOR_COACH,
            priority=8,
        ))

    # 通用: 自我效能崩塌 → 紧急接管
    rules.append(EscalationRule(
        condition="self_efficacy < 0.2 AND stage_stability < 0.3",
        action="handoff",
        target_agent=ExpertAgentType.BEHAVIOR_COACH,
        priority=10,
    ))

    # 领域特定
    if agent_type == ExpertAgentType.METABOLIC_EXPERT:
        rules.append(EscalationRule(
            condition="medication_missed > 3 times in 7 days",
            action="handoff",
            target_agent=ExpertAgentType.ADHERENCE_EXPERT,
            priority=7,
        ))
    elif agent_type == ExpertAgentType.CARDIAC_EXPERT:
        rules.append(EscalationRule(
            condition="exercise_fear_score > 0.8 AND avoidance_behavior detected",
            action="switch_strategy",
            priority=8,
        ))
        rules.append(EscalationRule(
            condition="heart_rate > safety_upper_bound",
            action="alert_coach",
            priority=10,
        ))

    # 高N特殊: 情绪危机预警
    if personality.is_high("N"):
        rules.append(EscalationRule(
            condition="negative_emotion_score > 0.85 for 2 consecutive sessions",
            action="alert_coach",
            priority=9,
        ))

    return rules


# =====================================================================
# BehaviorRxEngine — 主引擎
# =====================================================================

class BehaviorRxEngine:
    """
    行为处方核心引擎 — 所有 Expert Agent 的共享基座

    使用方式:
        engine = BehaviorRxEngine()
        rx = engine.compute_rx(context, agent_type)
        # rx 是 RxPrescriptionDTO, Agent 拿到后进行领域包装

    或异步:
        rx = await engine.compute_rx_async(context, agent_type, db)
    """

    def __init__(self, strategies_path: Optional[str] = None):
        """
        初始化引擎

        Args:
            strategies_path: rx_strategies.json 路径, None 则使用默认路径
        """
        self._strategy_templates: Dict[str, Dict] = {}
        self._load_strategy_templates(strategies_path)
        logger.info(
            f"BehaviorRxEngine initialized with {len(self._strategy_templates)} strategies"
        )

    def _load_strategy_templates(self, path: Optional[str] = None) -> None:
        """加载策略模板库"""
        if path is None:
            path = os.path.join(
                os.path.dirname(__file__), "..", "configs", "rx_strategies.json"
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for s in data.get("strategies", []):
                self._strategy_templates[s["strategy_type"]] = s
            logger.info(f"Loaded {len(self._strategy_templates)} strategy templates")
        except Exception as e:
            logger.warning(f"Failed to load strategy templates: {e}, using defaults")

    # ---------------------------------------------------------------
    # 核心方法: compute_rx — 三维处方计算
    # ---------------------------------------------------------------

    def compute_rx(
        self,
        context: RxContext,
        agent_type: ExpertAgentType,
        override_strategy: Optional[RxStrategyType] = None,
        override_intensity: Optional[RxIntensity] = None,
    ) -> RxPrescriptionDTO:
        """
        三维行为处方计算

        流程:
          1. 维度1: TTM阶段 → 选择策略类型 + 辅助策略
          2. 维度2: BigFive人格 → 确定沟通风格 + 策略微调
          3. 维度3: CAPACITY能力 → 校准强度 + 节奏 + 微行动难度
          4. 组装 → RxPrescriptionDTO

        Args:
            context: 三维输入上下文
            agent_type: 调用方 Agent 类型
            override_strategy: 强制指定策略 (跳过策略选择)
            override_intensity: 强制指定强度

        Returns:
            RxPrescriptionDTO 完整处方对象
        """
        stage = context.ttm_stage
        personality = context.personality
        capacity = context.capacity_score

        # ---- Step 1: 策略选择 (TTM 阶段驱动) ----
        primary_strategy, secondary_strategies = self._select_strategies(
            stage=stage,
            agent_type=agent_type,
            personality=personality,
            barriers=context.active_barriers,
            override=override_strategy,
        )

        # ---- Step 2: 沟通风格 (BigFive 驱动) ----
        comm_style = _determine_communication_style(personality)

        # ---- Step 3: 强度 & 节奏 (CAPACITY 驱动) ----
        capacity_band = "low" if capacity < 0.35 else ("high" if capacity > 0.65 else "mid")
        intensity = override_intensity or INTENSITY_MATRIX.get(
            stage, INTENSITY_MATRIX[3]
        ).get(capacity_band, RxIntensity.MODERATE)

        pace = _determine_pace(stage, capacity, context.stage_stability, personality)

        # ---- Step 4: 微行动生成 ----
        micro_actions = self._generate_micro_actions(
            primary_strategy, agent_type, capacity, personality, stage
        )

        # ---- Step 5: 奖励触发器 ----
        reward_triggers = self._generate_reward_triggers(
            primary_strategy, personality
        )

        # ---- Step 6: 阻力阈值 ----
        resistance_threshold = _calculate_resistance_threshold(
            personality, capacity, stage
        )

        # ---- Step 7: 升级规则 ----
        escalation_rules = _generate_escalation_rules(
            agent_type, stage, personality
        )

        # ---- Step 8: 目标行为描述 ----
        goal_behavior = self._formulate_goal_behavior(
            primary_strategy, agent_type, stage, context.domain_data
        )

        # ---- 组装处方 ----
        rx = RxPrescriptionDTO(
            rx_id=uuid.uuid4(),
            agent_type=agent_type,
            goal_behavior=goal_behavior,
            strategy_type=primary_strategy,
            secondary_strategies=secondary_strategies,
            intensity=intensity,
            pace=pace,
            communication_style=comm_style,
            micro_actions=micro_actions,
            reward_triggers=reward_triggers,
            resistance_threshold=resistance_threshold,
            escalation_rules=escalation_rules,
            domain_context=context.domain_data,
            ttm_stage=stage,
            confidence=self._calculate_confidence(context, primary_strategy),
            reasoning=self._generate_reasoning(
                stage, primary_strategy, comm_style, intensity, pace, personality
            ),
        )

        logger.info(
            f"RxPrescription computed: user={context.user_id} "
            f"agent={agent_type.value} stage=S{stage} "
            f"strategy={primary_strategy.value} intensity={intensity.value}"
        )
        return rx

    # ---------------------------------------------------------------
    # 异步版本 (含持久化)
    # ---------------------------------------------------------------

    async def compute_rx_async(
        self,
        context: RxContext,
        agent_type: ExpertAgentType,
        db=None,
        persist: bool = True,
        override_strategy: Optional[RxStrategyType] = None,
        override_intensity: Optional[RxIntensity] = None,
    ) -> RxPrescriptionDTO:
        """
        异步处方计算 + 可选持久化

        Args:
            db: SQLAlchemy AsyncSession (None 则不持久化)
            persist: 是否持久化到 rx_prescriptions 表
        """
        rx = self.compute_rx(context, agent_type, override_strategy, override_intensity)

        if persist and db is not None:
            await self._persist_rx(rx, context, db)

        return rx

    async def _persist_rx(self, rx: RxPrescriptionDTO, context: RxContext, db) -> None:
        """持久化处方到数据库"""
        try:
            # 动态导入避免循环依赖
            from .rx_models import RxPrescription as RxModel

            record = RxModel(
                id=rx.rx_id,
                user_id=context.user_id,
                session_id=context.session_id,
                agent_type=rx.agent_type.value,
                ttm_stage=rx.ttm_stage,
                bigfive_profile=context.personality.model_dump(),
                capacity_score=context.capacity_score,
                goal_behavior=rx.goal_behavior,
                strategy_type=rx.strategy_type.value,
                secondary_strategies=[s.value for s in rx.secondary_strategies],
                intensity=rx.intensity.value,
                pace=rx.pace,
                communication_style=rx.communication_style.value,
                micro_actions=[ma.model_dump() for ma in rx.micro_actions],
                reward_triggers=[rt.model_dump() for rt in rx.reward_triggers],
                resistance_threshold=rx.resistance_threshold,
                escalation_rules=[er.model_dump() for er in rx.escalation_rules],
                domain_context=rx.domain_context,
            )
            db.add(record)
            await db.flush()
            logger.info(f"RxPrescription persisted: {rx.rx_id}")
        except Exception as e:
            logger.error(f"Failed to persist RxPrescription: {e}")

    # ---------------------------------------------------------------
    # 策略选择逻辑
    # ---------------------------------------------------------------

    def _select_strategies(
        self,
        stage: int,
        agent_type: ExpertAgentType,
        personality: BigFiveProfile,
        barriers: List[str],
        override: Optional[RxStrategyType] = None,
    ) -> Tuple[RxStrategyType, List[RxStrategyType]]:
        """
        策略选择 — 综合阶段、Agent 类型、人格、障碍

        Returns:
            (primary_strategy, [secondary_strategies])
        """
        if override:
            candidates = STAGE_STRATEGY_MATRIX.get(stage, STAGE_STRATEGY_MATRIX[3])
            secondaries = [s for s in candidates if s != override][:2]
            return override, secondaries

        # 基础候选 (阶段驱动)
        candidates = list(STAGE_STRATEGY_MATRIX.get(stage, STAGE_STRATEGY_MATRIX[3]))

        # Agent 类型偏好
        agent_boosts = self._get_agent_strategy_preferences(agent_type)

        # 人格调节
        personality_scores = self._score_strategies_by_personality(
            candidates, personality
        )

        # 障碍驱动增强
        barrier_boosts = self._score_strategies_by_barriers(candidates, barriers)

        # 综合评分
        scores = {}
        for s in candidates:
            score = 1.0
            score += agent_boosts.get(s, 0)
            score += personality_scores.get(s, 0)
            score += barrier_boosts.get(s, 0)
            scores[s] = score

        # 排序选择
        sorted_strategies = sorted(scores, key=scores.get, reverse=True)
        primary = sorted_strategies[0]
        secondary = sorted_strategies[1:3]  # 最多2个辅助策略

        return primary, secondary

    def _get_agent_strategy_preferences(
        self, agent_type: ExpertAgentType
    ) -> Dict[RxStrategyType, float]:
        """Agent 类型的策略偏好加成"""
        prefs: Dict[ExpertAgentType, Dict[RxStrategyType, float]] = {
            ExpertAgentType.BEHAVIOR_COACH: {
                RxStrategyType.CONSCIOUSNESS_RAISING: 0.3,
                RxStrategyType.COGNITIVE_RESTRUCTURING: 0.25,
                RxStrategyType.DECISIONAL_BALANCE: 0.2,
                RxStrategyType.SELF_REEVALUATION: 0.2,
                RxStrategyType.SELF_LIBERATION: 0.15,
            },
            ExpertAgentType.METABOLIC_EXPERT: {
                RxStrategyType.STIMULUS_CONTROL: 0.3,
                RxStrategyType.SELF_MONITORING: 0.25,
                RxStrategyType.CONTINGENCY_MANAGEMENT: 0.2,
                RxStrategyType.HABIT_STACKING: 0.2,
            },
            ExpertAgentType.CARDIAC_EXPERT: {
                RxStrategyType.SYSTEMATIC_DESENSITIZATION: 0.35,
                RxStrategyType.STIMULUS_CONTROL: 0.2,
                RxStrategyType.SELF_MONITORING: 0.2,
                RxStrategyType.RELAPSE_PREVENTION: 0.15,
            },
            ExpertAgentType.ADHERENCE_EXPERT: {
                RxStrategyType.HABIT_STACKING: 0.3,
                RxStrategyType.STIMULUS_CONTROL: 0.25,
                RxStrategyType.CONTINGENCY_MANAGEMENT: 0.2,
                RxStrategyType.COGNITIVE_RESTRUCTURING: 0.15,
            },
        }
        return prefs.get(agent_type, {})

    def _score_strategies_by_personality(
        self, candidates: List[RxStrategyType], personality: BigFiveProfile
    ) -> Dict[RxStrategyType, float]:
        """人格特质对策略的评分调节"""
        scores: Dict[RxStrategyType, float] = {}
        for s in candidates:
            template = self._strategy_templates.get(s.value, {})
            mods = template.get("personality_modifiers", {})
            score = 0.0
            if personality.is_high("N") and "high_N" in mods:
                score += mods["high_N"].get("boost", 0)
            if personality.is_high("C") and "high_C" in mods:
                score += mods["high_C"].get("boost", 0)
            if personality.is_high("E") and "high_E" in mods:
                score += mods["high_E"].get("boost", 0)
            if personality.is_high("A") and "high_A" in mods:
                score += mods["high_A"].get("boost", 0)
            if personality.is_high("O") and "high_O" in mods:
                score += mods["high_O"].get("boost", 0)
            if personality.is_low("C") and "low_C" in mods:
                score += mods["low_C"].get("boost", 0)
            if personality.is_low("O") and "low_O" in mods:
                score += mods["low_O"].get("boost", 0)
            if personality.is_low("E") and "low_E" in mods:
                score += mods["low_E"].get("boost", 0)
            scores[s] = score
        return scores

    def _score_strategies_by_barriers(
        self, candidates: List[RxStrategyType], barriers: List[str]
    ) -> Dict[RxStrategyType, float]:
        """障碍类型对策略的增强评分"""
        barrier_strategy_map = {
            "fear": [RxStrategyType.SYSTEMATIC_DESENSITIZATION,
                     RxStrategyType.COGNITIVE_RESTRUCTURING],
            "forgetfulness": [RxStrategyType.HABIT_STACKING,
                              RxStrategyType.STIMULUS_CONTROL],
            "low_motivation": [RxStrategyType.DRAMATIC_RELIEF,
                               RxStrategyType.DECISIONAL_BALANCE],
            "cognitive": [RxStrategyType.CONSCIOUSNESS_RAISING,
                          RxStrategyType.COGNITIVE_RESTRUCTURING],
            "economic": [RxStrategyType.DECISIONAL_BALANCE],
            "relational": [RxStrategyType.SELF_LIBERATION],
        }
        scores: Dict[RxStrategyType, float] = {s: 0 for s in candidates}
        for barrier in barriers:
            for s in barrier_strategy_map.get(barrier, []):
                if s in scores:
                    scores[s] += 0.2
        return scores

    # ---------------------------------------------------------------
    # 微行动生成
    # ---------------------------------------------------------------

    def _generate_micro_actions(
        self,
        strategy: RxStrategyType,
        agent_type: ExpertAgentType,
        capacity: float,
        personality: BigFiveProfile,
        stage: int,
    ) -> List[MicroAction]:
        """
        生成微行动列表

        流程:
          1. 从策略模板获取默认微行动
          2. 根据 CAPACITY 校准难度
          3. 根据领域适配内容
        """
        template = self._strategy_templates.get(strategy.value, {})
        raw_actions = template.get("default_micro_actions", [])

        # 领域适配
        domain_key = {
            ExpertAgentType.METABOLIC_EXPERT: "metabolic",
            ExpertAgentType.CARDIAC_EXPERT: "cardiac",
            ExpertAgentType.ADHERENCE_EXPERT: "adherence",
        }.get(agent_type, "general")

        actions = []
        for ra in raw_actions:
            # CAPACITY 难度校准: 低能力 → 降低难度
            adjusted_difficulty = ra.get("difficulty", 0.3)
            if capacity < 0.3:
                adjusted_difficulty *= 0.6  # 低能力大幅降低
            elif capacity < 0.5:
                adjusted_difficulty *= 0.8
            elif capacity > 0.7:
                adjusted_difficulty *= 1.1  # 高能力适度提升

            adjusted_difficulty = max(0.05, min(0.9, adjusted_difficulty))

            actions.append(MicroAction(
                action=ra.get("action", ""),
                difficulty=round(adjusted_difficulty, 2),
                trigger=ra.get("trigger", ""),
                duration_min=ra.get("duration_min", 5),
                domain=domain_key,
            ))

        return actions

    # ---------------------------------------------------------------
    # 奖励触发器生成
    # ---------------------------------------------------------------

    def _generate_reward_triggers(
        self,
        strategy: RxStrategyType,
        personality: BigFiveProfile,
    ) -> List[RewardTrigger]:
        """从策略模板获取并个性化奖励触发器"""
        template = self._strategy_templates.get(strategy.value, {})
        raw_triggers = template.get("default_reward_triggers", [])

        triggers = []
        for rt in raw_triggers:
            # 人格适配: 高E/高A → 增加社交奖励
            reward_type = rt.get("reward_type", "praise")
            if personality.is_high("E") and reward_type == "praise":
                reward_type = "praise"  # 外向者更看重即时表扬
            if personality.is_high("C") and reward_type == "praise":
                reward_type = "badge"  # 尽责者更看重成就徽章

            triggers.append(RewardTrigger(
                condition=rt.get("condition", ""),
                reward_type=reward_type,
                message=rt.get("message", ""),
            ))

        return triggers

    # ---------------------------------------------------------------
    # 目标行为描述
    # ---------------------------------------------------------------

    def _formulate_goal_behavior(
        self,
        strategy: RxStrategyType,
        agent_type: ExpertAgentType,
        stage: int,
        domain_data: Dict[str, Any],
    ) -> str:
        """
        生成目标行为描述

        低阶段 (S0-S2): 认知/态度目标
        高阶段 (S3+): 行为执行目标
        """
        strategy_goals = {
            RxStrategyType.CONSCIOUSNESS_RAISING: "建立对健康行为重要性的基础认知",
            RxStrategyType.DRAMATIC_RELIEF: "通过情感体验激发改变动机",
            RxStrategyType.SELF_REEVALUATION: "重新审视当前行为与理想自我的一致性",
            RxStrategyType.DECISIONAL_BALANCE: "系统权衡改变的利弊并做出决定",
            RxStrategyType.COGNITIVE_RESTRUCTURING: "识别并修正阻碍行为改变的不合理信念",
            RxStrategyType.SELF_LIBERATION: "做出改变承诺并启动行动计划",
            RxStrategyType.STIMULUS_CONTROL: "通过环境重构降低行为执行障碍",
            RxStrategyType.CONTINGENCY_MANAGEMENT: "通过即时正强化巩固目标行为",
            RxStrategyType.HABIT_STACKING: "将新行为绑定到已有习惯形成自动化行为链",
            RxStrategyType.SYSTEMATIC_DESENSITIZATION: "通过渐进暴露消除恐惧回避行为",
            RxStrategyType.RELAPSE_PREVENTION: "建立高风险情境应对预案防止行为复发",
            RxStrategyType.SELF_MONITORING: "通过系统记录建立行为-结果意识",
        }
        base_goal = strategy_goals.get(strategy, "执行健康行为改变")

        # 领域上下文增强
        domain_suffix = {
            ExpertAgentType.METABOLIC_EXPERT: "在代谢管理领域",
            ExpertAgentType.CARDIAC_EXPERT: "在心血管康复领域",
            ExpertAgentType.ADHERENCE_EXPERT: "在医疗依从性领域",
            ExpertAgentType.BEHAVIOR_COACH: "在行为认知准备阶段",
        }.get(agent_type, "")

        return f"{domain_suffix}{base_goal}"

    # ---------------------------------------------------------------
    # 置信度计算
    # ---------------------------------------------------------------

    def _calculate_confidence(
        self, context: RxContext, strategy: RxStrategyType
    ) -> float:
        """
        计算处方置信度

        影响因素:
          - 数据完整度 (BAPS 评估是否完成)
          - 阶段稳定度
          - 策略-阶段匹配度
        """
        confidence = 0.7  # 基线

        # 阶段稳定度加成
        confidence += context.stage_stability * 0.15

        # 策略-阶段匹配度
        stage_strategies = STAGE_STRATEGY_MATRIX.get(context.ttm_stage, [])
        if strategy in stage_strategies:
            rank = stage_strategies.index(strategy)
            confidence += max(0, 0.1 - rank * 0.02)  # 排名越前越高

        # 数据完整度 (依从率作为代理指标)
        confidence += context.recent_adherence * 0.05

        return round(min(0.98, max(0.5, confidence)), 2)

    # ---------------------------------------------------------------
    # 处方推理说明
    # ---------------------------------------------------------------

    def _generate_reasoning(
        self,
        stage: int,
        strategy: RxStrategyType,
        comm_style: CommunicationStyle,
        intensity: RxIntensity,
        pace: str,
        personality: BigFiveProfile,
    ) -> str:
        """生成处方推理说明 (用于决策审计和透明性)"""
        dominant = personality.dominant_trait()
        trait_names = {"O": "开放性", "C": "尽责性", "E": "外向性",
                       "A": "宜人性", "N": "神经质"}
        return (
            f"三维计算: TTM-S{stage}阶段 → 选择{strategy.value}策略; "
            f"BigFive主导特质{trait_names.get(dominant, dominant)} "
            f"→ {comm_style.value}沟通风格; "
            f"能力评估 → {intensity.value}强度/{pace}节奏"
        )

    # ---------------------------------------------------------------
    # 处方更新 (策略切换)
    # ---------------------------------------------------------------

    def switch_strategy(
        self,
        current_rx: RxPrescriptionDTO,
        context: RxContext,
        reason: str = "resistance_exceeded",
    ) -> RxPrescriptionDTO:
        """
        策略切换 — 当阻力超标时切换到下一个候选策略

        Args:
            current_rx: 当前处方
            context: 当前上下文
            reason: 切换原因

        Returns:
            新的 RxPrescriptionDTO (supersedes 当前处方)
        """
        stage_strategies = STAGE_STRATEGY_MATRIX.get(context.ttm_stage, [])
        current_idx = -1
        for i, s in enumerate(stage_strategies):
            if s == current_rx.strategy_type:
                current_idx = i
                break

        # 选下一个策略
        next_idx = (current_idx + 1) % len(stage_strategies)
        next_strategy = stage_strategies[next_idx]

        logger.info(
            f"Strategy switch: {current_rx.strategy_type.value} → "
            f"{next_strategy.value} reason={reason}"
        )

        return self.compute_rx(
            context=context,
            agent_type=current_rx.agent_type,
            override_strategy=next_strategy,
        )

    # ---------------------------------------------------------------
    # 处方效果评估
    # ---------------------------------------------------------------

    def evaluate_effectiveness(
        self,
        rx: RxPrescriptionDTO,
        adherence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        评估处方有效性

        Args:
            rx: 处方
            adherence_data: 依从数据 {
                micro_action_completion_rate: float,
                days_active: int,
                stage_change: int,
                resistance_events: int,
            }

        Returns:
            {ies_score, adherence_index, recommendation}
        """
        completion = adherence_data.get("micro_action_completion_rate", 0)
        days = adherence_data.get("days_active", 0)
        stage_change = adherence_data.get("stage_change", 0)
        resistance = adherence_data.get("resistance_events", 0)

        # IES 综合评分
        ies = 0.0
        ies += completion * 0.4  # 微行动完成率权重最大
        ies += min(days / 30, 1.0) * 0.2  # 持续天数
        ies += max(0, min(stage_change + 1, 3)) / 3 * 0.25  # 阶段进展
        ies -= min(resistance / 10, 0.3) * 0.15  # 阻力惩罚

        ies = round(max(0, min(1, ies)), 3)

        # 建议
        if ies >= 0.7:
            recommendation = "continue"
        elif ies >= 0.4:
            recommendation = "adjust"
        else:
            recommendation = "switch_strategy"

        return {
            "ies_score": ies,
            "adherence_index": round(completion, 3),
            "recommendation": recommendation,
            "details": {
                "completion_contribution": round(completion * 0.4, 3),
                "duration_contribution": round(min(days / 30, 1.0) * 0.2, 3),
                "progress_contribution": round(max(0, min(stage_change + 1, 3)) / 3 * 0.25, 3),
                "resistance_penalty": round(min(resistance / 10, 0.3) * 0.15, 3),
            },
        }
