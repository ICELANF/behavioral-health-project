"""
Agent基础类型定义
来源: §9 十二专业Agent体系, §10 多Agent协调, §11 策略闸门
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


# ── 风险等级 (§11.4) ──
class RiskLevel(str, Enum):
    CRITICAL = "critical"    # 危急: 需要立即干预
    HIGH = "high"            # 高风险: 优先处理, 共情风格
    MODERATE = "moderate"    # 中等: 常规处理
    LOW = "low"              # 低风险: 维护性干预


# ── Agent领域 ──
class AgentDomain(str, Enum):
    CRISIS = "crisis"
    SLEEP = "sleep"
    GLUCOSE = "glucose"
    STRESS = "stress"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    MENTAL = "mental"
    TCM = "tcm"
    MOTIVATION = "motivation"
    BEHAVIOR_RX = "behavior_rx"
    WEIGHT = "weight"
    CARDIAC_REHAB = "cardiac_rehab"


# ── 策略闸门决策类型 (§11.2) ──
class PolicyDecision(str, Enum):
    ALLOW = "allow"                       # 正常允许
    DELAY = "delay"                       # 延迟(状态不稳定)
    ALLOW_SOFT_SUPPORT = "allow_soft"     # 只允许共情/软支持
    ESCALATE_COACH = "escalate_coach"     # 升级到教练
    DENY = "deny"                         # 拒绝


# ── 冲突类型 (§10.2) ──
class ConflictType(str, Enum):
    CONTRADICTION = "contradiction"  # 观点矛盾
    OVERLAP = "overlap"              # 建议重叠
    PRIORITY = "priority"            # 优先级冲突


# ── Agent输入 ──
@dataclass
class AgentInput:
    user_id: int
    message: str
    intent: str = ""
    profile: dict = field(default_factory=dict)
    device_data: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)


# ── Agent输出 ──
@dataclass
class AgentResult:
    agent_domain: str
    confidence: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_domain": self.agent_domain,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "tasks": self.tasks,
            "metadata": self.metadata,
        }


# ── Agent基类 ──
class BaseAgent:
    """所有Agent的基类"""

    domain: AgentDomain
    display_name: str = ""
    keywords: list[str] = []
    data_fields: list[str] = []
    priority: int = 5           # 0=最高
    base_weight: float = 0.8    # §10.1 权重

    def process(self, agent_input: AgentInput) -> AgentResult:
        raise NotImplementedError

    def matches_intent(self, message: str) -> bool:
        """关键词匹配"""
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in self.keywords)


# ── Agent权重表 (§10.1) ──
AGENT_BASE_WEIGHTS: dict[str, float] = {
    "crisis": 1.0,
    "glucose": 0.9,
    "sleep": 0.85,
    "stress": 0.85,
    "mental": 0.85,
    "nutrition": 0.8,
    "exercise": 0.8,
    "tcm": 0.75,
    "motivation": 0.8,
    "behavior_rx": 0.9,
    "weight": 0.85,
    "cardiac_rehab": 0.85,
}


# ── 领域关联网络 (§9.2) ──
DOMAIN_CORRELATIONS: dict[str, list[str]] = {
    "sleep":        ["glucose", "stress", "mental", "exercise"],
    "glucose":      ["sleep", "nutrition", "exercise", "weight", "stress"],
    "stress":       ["sleep", "mental", "exercise", "cardiac_rehab"],
    "nutrition":    ["glucose", "exercise", "weight", "tcm"],
    "exercise":     ["glucose", "stress", "sleep", "weight", "cardiac_rehab"],
    "mental":       ["stress", "sleep", "behavior_rx", "motivation"],
    "tcm":          ["nutrition", "sleep", "mental", "stress"],
    "crisis":       ["mental", "stress", "behavior_rx"],
    "behavior_rx":  ["mental", "motivation", "nutrition", "exercise",
                     "sleep", "glucose", "weight", "tcm", "stress"],
    "weight":       ["nutrition", "exercise", "glucose", "sleep",
                     "mental", "motivation", "behavior_rx", "tcm"],
    "cardiac_rehab": ["exercise", "stress", "sleep", "nutrition",
                      "mental", "glucose", "weight", "motivation", "behavior_rx"],
}


# ── 冲突消解优先级 (§10.3) ──
CONFLICT_PRIORITY: dict[tuple[str, str], str] = {
    ("glucose", "nutrition"): "glucose",
    ("sleep", "exercise"): "sleep",
    ("stress", "exercise"): "stress",
    ("mental", "exercise"): "mental",
}
