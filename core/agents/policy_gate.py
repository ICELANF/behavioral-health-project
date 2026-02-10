"""
RuntimePolicyGate — 策略闸门
来源: §11 策略闸门与安全保护

核心原则: 所有干预决策必须经过策略闸门

规则链 (§11.3, 按优先级):
  #1 不稳定态 + 强干预请求 → DELAY
  #2 S0-S1阶段 → ALLOW_SOFT_SUPPORT (禁止challenge/execution)
  #3 dropout_risk + S3+ → ESCALATE_COACH
  #4 relapse_risk → ALLOW_SOFT_SUPPORT
  #5 其余 → ALLOW
"""
from __future__ import annotations
from dataclasses import dataclass
from .base import PolicyDecision, RiskLevel


@dataclass
class GateResult:
    decision: PolicyDecision
    reason: str
    allowed_modes: list[str]    # 允许的交互模式
    metadata: dict = None

    def __post_init__(self):
        self.metadata = self.metadata or {}


class RuntimePolicyGate:
    """
    所有干预方案在下发给用户前必须经过策略闸门审查
    """

    def evaluate(self,
                 current_stage: str,
                 stability: str = "stable",
                 intervention_strength: str = "normal",
                 dropout_risk: bool = False,
                 relapse_risk: bool = False,
                 risk_level: str = "low") -> GateResult:
        """
        Args:
            current_stage: S0-S6
            stability: "stable" | "unstable" | "critical"
            intervention_strength: "soft" | "normal" | "challenge"
            dropout_risk: 是否有退出风险
            relapse_risk: 是否有复发风险
            risk_level: RiskLevel value
        """

        # 规则 #0: 危机状态 — 直接放行(CrisisAgent已接管)
        if risk_level == "critical":
            return GateResult(
                decision=PolicyDecision.ALLOW,
                reason="危机状态, CrisisAgent接管",
                allowed_modes=["crisis_support"],
            )

        # 规则 #1: 不稳定态 + 强干预
        if stability in ("unstable", "critical") and intervention_strength == "challenge":
            return GateResult(
                decision=PolicyDecision.DELAY,
                reason="用户状态不稳定, 延迟强干预, 等待稳定后再执行",
                allowed_modes=[],
            )

        # 规则 #2: S0-S1 早期阶段 — 只允许软支持
        if current_stage in ("S0", "S1"):
            return GateResult(
                decision=PolicyDecision.ALLOW_SOFT_SUPPORT,
                reason="早期阶段(S0-S1), 仅允许共情/探索式交互",
                allowed_modes=["empathy", "exploration"],
            )

        # 规则 #3: 有退出风险 + S3以上 → 升级教练
        if dropout_risk and current_stage in ("S3", "S4", "S5", "S6"):
            return GateResult(
                decision=PolicyDecision.ESCALATE_COACH,
                reason="检测到退出风险, 升级至教练人工介入",
                allowed_modes=["empathy", "coach_support"],
            )

        # 规则 #4: 复发风险 → 软支持
        if relapse_risk:
            return GateResult(
                decision=PolicyDecision.ALLOW_SOFT_SUPPORT,
                reason="复发风险下只允许软支持, 避免施压",
                allowed_modes=["empathy", "maintenance"],
            )

        # 规则 #5: 正常放行
        return GateResult(
            decision=PolicyDecision.ALLOW,
            reason="正常放行",
            allowed_modes=["empathy", "challenge", "execution"],
        )
