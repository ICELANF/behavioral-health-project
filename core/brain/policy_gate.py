# -*- coding: utf-8 -*-
"""
RuntimePolicyGate - 策略闸门

职责:
- 所有干预必须过闸门
- 基于 RuntimeState 决定: 允许/延迟/软支持/升级教练/拒绝
- 保护不稳定状态下的用户不被强干预伤害

设计原则:
  不稳定态 → DELAY（禁止强干预）
  S0-S1 → ALLOW_SOFT_SUPPORT（只能共情，不能挑战）
  dropout_risk + S3+ → ESCALATE_COACH（升级到教练）
  正常 → ALLOW
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from loguru import logger

from core.brain.stage_runtime import RuntimeState, STAGE_INDEX


class PolicyDecisionType(str, Enum):
    """策略决定类型"""
    ALLOW = "allow"                     # 正常允许
    DELAY = "delay"                     # 延迟（状态不稳定）
    ALLOW_SOFT_SUPPORT = "soft_support" # 只允许共情/软支持
    ESCALATE_COACH = "escalate_coach"   # 升级到教练
    DENY = "deny"                       # 拒绝


@dataclass
class PolicyDecision:
    """策略闸门决定"""
    action: PolicyDecisionType
    reason: str
    intervention_allowed: bool  # 是否允许发出干预
    escalation_target: Optional[str] = None  # 升级目标: "coach" / "supervisor"
    allowed_modes: Optional[list] = None  # 允许的交互模式


class RuntimePolicyGate:
    """
    策略闸门 — 所有干预决策必须经过此闸门

    规则链 (按优先级从高到低):
    1. 不稳定态 + 强干预 → DELAY
    2. S0-S1 → ALLOW_SOFT_SUPPORT（禁止 CHALLENGE/EXECUTION）
    3. dropout_risk + S3+ → ESCALATE_COACH
    4. relapse_risk → ALLOW_SOFT_SUPPORT
    5. 其余 → ALLOW
    """

    def evaluate(
        self,
        runtime_state: RuntimeState,
        recommended_mode: Optional[str] = None,
        source: Optional[str] = None,
    ) -> PolicyDecision:
        """
        评估干预是否被允许

        Args:
            runtime_state: StageRuntimeBuilder 输出的运行态
            recommended_mode: 推荐的交互模式 (empathy/challenge/execution)
            source: 请求来源 (api/agent/system)

        Returns:
            PolicyDecision
        """
        stage = runtime_state.confirmed_stage
        stability = runtime_state.stability
        risk_flags = runtime_state.risk_flags
        stage_idx = STAGE_INDEX.get(stage, 0)

        # 规则 1: 不稳定态 + 强干预请求 → DELAY
        if stability == "unstable" and recommended_mode in ("challenge", "execution"):
            logger.info(
                f"PolicyGate DELAY: user={runtime_state.user_id}, "
                f"stage={stage}, unstable + {recommended_mode}"
            )
            return PolicyDecision(
                action=PolicyDecisionType.DELAY,
                reason=f"Stage {stage} is unstable, strong intervention delayed",
                intervention_allowed=False,
                allowed_modes=["empathy"],
            )

        # 规则 2: S0-S1 → 只允许共情/软支持
        if stage_idx <= 1:
            if recommended_mode in ("challenge", "execution"):
                logger.info(
                    f"PolicyGate SOFT_SUPPORT: user={runtime_state.user_id}, "
                    f"stage={stage}, early stage cannot use {recommended_mode}"
                )
                return PolicyDecision(
                    action=PolicyDecisionType.ALLOW_SOFT_SUPPORT,
                    reason=f"Early stage {stage}: only soft support allowed",
                    intervention_allowed=True,
                    allowed_modes=["empathy"],
                )

        # 规则 3: dropout_risk + S3+ → 升级教练
        if "dropout_risk" in risk_flags and stage_idx >= 3:
            logger.info(
                f"PolicyGate ESCALATE: user={runtime_state.user_id}, "
                f"stage={stage}, dropout_risk detected"
            )
            return PolicyDecision(
                action=PolicyDecisionType.ESCALATE_COACH,
                reason=f"Dropout risk at {stage}, escalating to coach",
                intervention_allowed=True,
                escalation_target="coach",
                allowed_modes=["empathy", "challenge"],
            )

        # 规则 4: relapse_risk → 软支持
        if "relapse_risk" in risk_flags:
            logger.info(
                f"PolicyGate SOFT_SUPPORT: user={runtime_state.user_id}, "
                f"stage={stage}, relapse_risk"
            )
            return PolicyDecision(
                action=PolicyDecisionType.ALLOW_SOFT_SUPPORT,
                reason=f"Relapse risk at {stage}: soft support recommended",
                intervention_allowed=True,
                allowed_modes=["empathy"],
            )

        # 规则 5: 正常放行
        return PolicyDecision(
            action=PolicyDecisionType.ALLOW,
            reason="All checks passed",
            intervention_allowed=True,
            allowed_modes=["empathy", "challenge", "execution"],
        )
