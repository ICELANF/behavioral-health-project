"""
Agent基础类型定义
来源: §9 十二专业Agent体系, §10 多Agent协调, §11 策略闸门
"""
from __future__ import annotations
import logging
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


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
    VISION = "vision"
    XZB_EXPERT = "xzb_expert"
    # Phase 3: 用户层 Agent
    HEALTH_ASSISTANT = "health_assistant"
    HABIT_TRACKER = "habit_tracker"
    ONBOARDING_GUIDE = "onboarding_guide"


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
    llm_enhanced: bool = False
    llm_latency_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "agent_domain": self.agent_domain,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "tasks": self.tasks,
            "metadata": self.metadata,
            "llm_enhanced": self.llm_enhanced,
            "llm_latency_ms": self.llm_latency_ms,
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
    enable_llm: bool = True     # LLM 增强开关 (CrisisAgent 关闭)
    evidence_tier: str = "T3"   # I-09: 循证等级 T1/T2/T3/T4

    # I-09: 循证等级置信度乘数
    _EVIDENCE_MULTIPLIERS = {"T1": 1.0, "T2": 0.9, "T3": 0.75, "T4": 0.5}

    def get_effective_confidence(self, raw_confidence: float) -> float:
        """I-09: 根据循证等级调整置信度"""
        multiplier = self._EVIDENCE_MULTIPLIERS.get(self.evidence_tier, 0.75)
        return round(raw_confidence * multiplier, 4)

    def process(self, agent_input: AgentInput) -> AgentResult:
        raise NotImplementedError

    def matches_intent(self, message: str) -> bool:
        """关键词匹配"""
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in self.keywords)

    def _enhance_with_llm(self, result: AgentResult, inp: AgentInput) -> AgentResult:
        """
        用 LLM 增强 recommendations 文本。
        路由: UnifiedLLMClient (云优先 → 本地降级)
        - 不修改 findings / risk_level / tasks
        - 任何异常静默返回原始 result
        """
        if not self.enable_llm:
            return result

        try:
            from core.llm_client import get_llm_client
            from .prompts import DOMAIN_SYSTEM_PROMPTS, build_agent_enhancement_prompt

            client = get_llm_client()
            if not client.is_available():
                return result

            # 优先级: _template_system_prompt > DOMAIN_SYSTEM_PROMPTS[domain]
            system_prompt = getattr(self, '_template_system_prompt', None)
            if not system_prompt:
                system_prompt = DOMAIN_SYSTEM_PROMPTS.get(self.domain.value, "") if self.domain else ""
            if not system_prompt:
                return result

            user_prompt = build_agent_enhancement_prompt(
                user_message=inp.message,
                findings=result.findings,
                recommendations=result.recommendations,
                device_data=inp.device_data,
            )

            resp = client.chat(system_prompt, user_prompt)
            if not resp.success or not resp.content:
                return result

            # 解析 LLM 输出: 每行 "- xxx" 作为一条建议
            new_recs = []
            for line in resp.content.strip().splitlines():
                line = line.strip()
                if line.startswith("- "):
                    new_recs.append(line[2:].strip())
                elif line.startswith("* "):
                    new_recs.append(line[2:].strip())
                elif line and not line.startswith("#"):
                    new_recs.append(line)

            if new_recs:
                result.recommendations = new_recs[:5]
                result.llm_enhanced = True
                result.llm_latency_ms = resp.latency_ms
                result.metadata["llm_model"] = resp.model
                result.metadata["llm_provider"] = resp.provider

            return result

        except Exception as e:
            logger.warning("Agent %s LLM enhancement failed: %s", self.domain.value, e)
            return result


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
    "vision": 0.8,
    "xzb_expert": 0.95,
    # Phase 3: 用户层 Agent
    "health_assistant": 0.65,
    "habit_tracker": 0.6,
    "onboarding_guide": 0.7,
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
    "vision":       ["sleep", "exercise", "behavior_rx", "nutrition"],
    # Phase 3: 用户层 Agent
    "health_assistant": ["nutrition", "tcm", "exercise", "sleep"],
    "habit_tracker":    ["behavior_rx", "motivation"],
    "onboarding_guide": ["trust_guide", "motivation", "health_assistant"],
}


# ── 冲突消解优先级 (§10.3) ──
CONFLICT_PRIORITY: dict[tuple[str, str], str] = {
    ("glucose", "nutrition"): "glucose",
    ("sleep", "exercise"): "sleep",
    ("stress", "exercise"): "stress",
    ("mental", "exercise"): "mental",
}


# ── Agent 类注册表 — 预置 Agent 类映射 ──
AGENT_CLASS_REGISTRY: dict[str, type] = {}
