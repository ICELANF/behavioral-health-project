"""
BehaviorOS — RxConflictResolver 行为处方冲突解决器
=====================================================
扩展 V007 ConflictResolver, 增加第 6 种冲突仲裁策略: behavioral_priority

现有 V007 5 种策略:
  1. weighted_score    — 加权评分
  2. priority_tree     — 优先级树
  3. medical_boundary  — 医疗边界
  4. tenant_override   — 租户覆盖
  5. risk_suppress     — 风险抑制

新增第 6 种:
  6. behavioral_priority — 行为处方优先级

设计原则:
  - 行为处方冲突发生在多Agent并行产出处方时
  - 安全永远最高优先 (medical_boundary 仍然覆盖 behavioral_priority)
  - 同策略不同强度 → 保守原则 (取较低强度)
  - 冲突策略 → 阶段适配原则 (选择更适合当前TTM阶段的策略)
  - 矛盾指令 → Coach裁决 (行为教练有最终裁决权)

集成方式:
  在 v31 conflict_resolver.py 的 ConflictResolver.resolve() 中
  添加 "behavioral_priority" 策略分支
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..core.rx_schemas import (
    ExpertAgentType,
    RxIntensity,
    RxPrescriptionDTO,
    RxStrategyType,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 策略优先级映射 (TTM 阶段 → 推荐策略排序)
# =====================================================================

# 每个 TTM 阶段的策略适用性排序 (前面的优先)
STAGE_STRATEGY_PRIORITY = {
    0: [  # 前意识
        RxStrategyType.CONSCIOUSNESS_RAISING,
        RxStrategyType.DRAMATIC_RELIEF,
        RxStrategyType.SELF_REEVALUATION,
    ],
    1: [  # 意识
        RxStrategyType.DECISIONAL_BALANCE,
        RxStrategyType.SELF_REEVALUATION,
        RxStrategyType.CONSCIOUSNESS_RAISING,
        RxStrategyType.COGNITIVE_RESTRUCTURING,
    ],
    2: [  # 准备
        RxStrategyType.SELF_LIBERATION,
        RxStrategyType.COGNITIVE_RESTRUCTURING,
        RxStrategyType.DECISIONAL_BALANCE,
        RxStrategyType.SYSTEMATIC_DESENSITIZATION,
    ],
    3: [  # 行动
        RxStrategyType.STIMULUS_CONTROL,
        RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.HABIT_STACKING,
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.SYSTEMATIC_DESENSITIZATION,
    ],
    4: [  # 维持
        RxStrategyType.RELAPSE_PREVENTION,
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.HABIT_STACKING,
    ],
    5: [  # 习惯化
        RxStrategyType.SELF_MONITORING,
        RxStrategyType.RELAPSE_PREVENTION,
    ],
    6: [  # 终止
        RxStrategyType.SELF_MONITORING,
    ],
}

# 强度等级排序 (从保守到激进)
INTENSITY_ORDER = {
    RxIntensity.MINIMAL: 0,
    RxIntensity.LOW: 1,
    RxIntensity.MODERATE: 2,
    RxIntensity.HIGH: 3,
    RxIntensity.INTENSIVE: 4,
}

# Agent 裁决优先级 (Coach 最高)
AGENT_ARBITRATION_PRIORITY = {
    ExpertAgentType.BEHAVIOR_COACH: 10,
    ExpertAgentType.ADHERENCE_EXPERT: 7,
    ExpertAgentType.CARDIAC_EXPERT: 5,
    ExpertAgentType.METABOLIC_EXPERT: 5,
}


# =====================================================================
# 冲突类型
# =====================================================================

class RxConflictType:
    """行为处方冲突类型"""
    STRATEGY_MISMATCH = "strategy_mismatch"       # 策略不一致
    INTENSITY_MISMATCH = "intensity_mismatch"     # 强度不一致
    DIRECTIVE_CONFLICT = "directive_conflict"       # 指令矛盾
    PACE_CONFLICT = "pace_conflict"                # 节奏冲突
    NO_CONFLICT = "no_conflict"                    # 无冲突


class RxConflictResult:
    """冲突解决结果"""

    def __init__(
        self,
        conflict_type: str,
        resolved_rx: RxPrescriptionDTO,
        arbitration_reason: str,
        winning_agent: ExpertAgentType,
        conflict_details: Dict[str, Any],
    ):
        self.conflict_type = conflict_type
        self.resolved_rx = resolved_rx
        self.arbitration_reason = arbitration_reason
        self.winning_agent = winning_agent
        self.conflict_details = conflict_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "arbitration_reason": self.arbitration_reason,
            "winning_agent": self.winning_agent.value,
            "resolved_strategy": self.resolved_rx.strategy_type.value,
            "resolved_intensity": self.resolved_rx.intensity.value,
            "conflict_details": self.conflict_details,
        }


# =====================================================================
# RxConflictResolver — 行为处方冲突解决器
# =====================================================================

class RxConflictResolver:
    """
    行为处方冲突解决器

    处理多Agent并行产出处方时的冲突:
      1. 策略冲突 → 阶段适配原则
      2. 强度冲突 → 保守原则
      3. 指令矛盾 → Coach裁决
      4. 无冲突 → 主Agent优先

    使用方式:
      resolver = RxConflictResolver()
      result = resolver.resolve(
          prescriptions=[rx_a, rx_b],
          ttm_stage=3,
          primary_agent=ExpertAgentType.METABOLIC_EXPERT,
      )
    """

    def resolve(
        self,
        prescriptions: List[RxPrescriptionDTO],
        ttm_stage: int,
        primary_agent: Optional[ExpertAgentType] = None,
    ) -> RxConflictResult:
        """
        解决多处方冲突

        Args:
            prescriptions: 多个Agent产出的处方列表
            ttm_stage: 当前TTM阶段
            primary_agent: 主导Agent (合并时优先)

        Returns:
            RxConflictResult 包含解决后的处方
        """
        if len(prescriptions) == 0:
            raise ValueError("至少需要一个处方")

        if len(prescriptions) == 1:
            return RxConflictResult(
                conflict_type=RxConflictType.NO_CONFLICT,
                resolved_rx=prescriptions[0],
                arbitration_reason="单处方, 无需仲裁",
                winning_agent=prescriptions[0].agent_type,
                conflict_details={},
            )

        # 检测冲突类型
        conflict_type = self._detect_conflict(prescriptions)

        if conflict_type == RxConflictType.NO_CONFLICT:
            winner = self._select_primary(prescriptions, primary_agent)
            return RxConflictResult(
                conflict_type=RxConflictType.NO_CONFLICT,
                resolved_rx=winner,
                arbitration_reason="处方一致, 选择主Agent版本",
                winning_agent=winner.agent_type,
                conflict_details={},
            )

        if conflict_type == RxConflictType.INTENSITY_MISMATCH:
            return self._resolve_intensity(
                prescriptions, primary_agent
            )

        if conflict_type == RxConflictType.STRATEGY_MISMATCH:
            return self._resolve_strategy(
                prescriptions, ttm_stage, primary_agent
            )

        # DIRECTIVE_CONFLICT / PACE_CONFLICT → Coach裁决
        return self._resolve_by_coach_arbitration(
            prescriptions, primary_agent
        )

    # ---------------------------------------------------------------
    # 冲突检测
    # ---------------------------------------------------------------

    def _detect_conflict(
        self, prescriptions: List[RxPrescriptionDTO]
    ) -> str:
        """检测处方间冲突类型"""
        strategies = {rx.strategy_type for rx in prescriptions}
        intensities = {rx.intensity for rx in prescriptions}
        goals = {rx.goal_behavior for rx in prescriptions}

        if len(strategies) > 1:
            return RxConflictType.STRATEGY_MISMATCH

        if len(intensities) > 1:
            return RxConflictType.INTENSITY_MISMATCH

        # 检查指令矛盾 (不同目标行为可能矛盾)
        if len(goals) > 1:
            return RxConflictType.DIRECTIVE_CONFLICT

        return RxConflictType.NO_CONFLICT

    # ---------------------------------------------------------------
    # 强度冲突 → 保守原则
    # ---------------------------------------------------------------

    def _resolve_intensity(
        self,
        prescriptions: List[RxPrescriptionDTO],
        primary_agent: Optional[ExpertAgentType],
    ) -> RxConflictResult:
        """保守原则: 取较低强度"""
        sorted_rx = sorted(
            prescriptions,
            key=lambda rx: INTENSITY_ORDER.get(rx.intensity, 2),
        )
        winner = sorted_rx[0]  # 最低强度

        details = {
            "intensities": {
                rx.agent_type.value: rx.intensity.value
                for rx in prescriptions
            },
            "resolution": "conservative_principle",
        }

        return RxConflictResult(
            conflict_type=RxConflictType.INTENSITY_MISMATCH,
            resolved_rx=winner,
            arbitration_reason=(
                f"保守原则: 从{len(prescriptions)}个强度中"
                f"选择最保守的 {winner.intensity.value}"
            ),
            winning_agent=winner.agent_type,
            conflict_details=details,
        )

    # ---------------------------------------------------------------
    # 策略冲突 → 阶段适配原则
    # ---------------------------------------------------------------

    def _resolve_strategy(
        self,
        prescriptions: List[RxPrescriptionDTO],
        ttm_stage: int,
        primary_agent: Optional[ExpertAgentType],
    ) -> RxConflictResult:
        """阶段适配原则: 选择最适合当前TTM阶段的策略"""
        priority_list = STAGE_STRATEGY_PRIORITY.get(ttm_stage, [])

        best_rx = None
        best_rank = 999

        for rx in prescriptions:
            if rx.strategy_type in priority_list:
                rank = priority_list.index(rx.strategy_type)
            else:
                rank = 100  # 不在推荐列表中
            if rank < best_rank:
                best_rank = rank
                best_rx = rx

        if best_rx is None:
            best_rx = self._select_primary(prescriptions, primary_agent)

        details = {
            "strategies": {
                rx.agent_type.value: rx.strategy_type.value
                for rx in prescriptions
            },
            "stage": ttm_stage,
            "stage_priority_list": [s.value for s in priority_list],
            "resolution": "stage_adaptation_principle",
        }

        return RxConflictResult(
            conflict_type=RxConflictType.STRATEGY_MISMATCH,
            resolved_rx=best_rx,
            arbitration_reason=(
                f"阶段适配: S{ttm_stage}阶段优先策略 "
                f"{best_rx.strategy_type.value}"
            ),
            winning_agent=best_rx.agent_type,
            conflict_details=details,
        )

    # ---------------------------------------------------------------
    # 指令矛盾 → Coach裁决
    # ---------------------------------------------------------------

    def _resolve_by_coach_arbitration(
        self,
        prescriptions: List[RxPrescriptionDTO],
        primary_agent: Optional[ExpertAgentType],
    ) -> RxConflictResult:
        """Coach裁决: 行为教练有最终裁决权"""
        # 按 Agent 优先级排序
        sorted_rx = sorted(
            prescriptions,
            key=lambda rx: AGENT_ARBITRATION_PRIORITY.get(
                rx.agent_type, 0
            ),
            reverse=True,
        )
        winner = sorted_rx[0]

        details = {
            "agent_priorities": {
                rx.agent_type.value: AGENT_ARBITRATION_PRIORITY.get(
                    rx.agent_type, 0
                )
                for rx in prescriptions
            },
            "resolution": "coach_arbitration",
        }

        return RxConflictResult(
            conflict_type=RxConflictType.DIRECTIVE_CONFLICT,
            resolved_rx=winner,
            arbitration_reason=(
                f"Coach裁决: {winner.agent_type.value} "
                f"(优先级 {AGENT_ARBITRATION_PRIORITY.get(winner.agent_type, 0)})"
            ),
            winning_agent=winner.agent_type,
            conflict_details=details,
        )

    # ---------------------------------------------------------------
    # 主Agent选择
    # ---------------------------------------------------------------

    def _select_primary(
        self,
        prescriptions: List[RxPrescriptionDTO],
        primary_agent: Optional[ExpertAgentType],
    ) -> RxPrescriptionDTO:
        """选择主Agent的处方"""
        if primary_agent:
            for rx in prescriptions:
                if rx.agent_type == primary_agent:
                    return rx
        return prescriptions[0]


# =====================================================================
# V007 ConflictResolver 集成补丁
# =====================================================================

def integrate_behavioral_priority(existing_resolver_class):
    """
    为 V007 ConflictResolver 添加 behavioral_priority 策略

    使用方式 (在 v31 启动时调用):
        from core.conflict_resolver import ConflictResolver
        from behavior_rx.core.rx_conflict_resolver import integrate_behavioral_priority
        integrate_behavioral_priority(ConflictResolver)

    这样 PolicyEngine 在冲突矩阵中配置 strategy="behavioral_priority" 时,
    就会调用 RxConflictResolver 进行行为处方级别的冲突仲裁。
    """
    rx_resolver = RxConflictResolver()

    original_resolve = existing_resolver_class.resolve

    def patched_resolve(self, conflicts, strategy="weighted_score", **kwargs):
        if strategy == "behavioral_priority":
            # 提取处方对象
            prescriptions = kwargs.get("prescriptions", [])
            ttm_stage = kwargs.get("ttm_stage", 3)
            primary_agent = kwargs.get("primary_agent", None)

            if prescriptions:
                result = rx_resolver.resolve(
                    prescriptions=prescriptions,
                    ttm_stage=ttm_stage,
                    primary_agent=primary_agent,
                )
                return {
                    "strategy": "behavioral_priority",
                    "result": result.to_dict(),
                    "resolved_rx": result.resolved_rx,
                }

        # 回退到原始方法
        return original_resolve(self, conflicts, strategy, **kwargs)

    existing_resolver_class.resolve = patched_resolve
    logger.info("V007 ConflictResolver patched with behavioral_priority strategy")
