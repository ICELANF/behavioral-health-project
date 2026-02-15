"""
F-010: BPT-6 Routing Schema — 行为分型到干预路径映射

Source: 契约注册表 ⑥ Rx引擎 Sheet
三维→四维: TTM-Stage × Domain × AgencyMode (× RiskLevel)
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class BPTDomain(str, Enum):
    """BPT-6 六大干预域"""
    nutrition = "nutrition"      # 营养
    exercise = "exercise"        # 运动
    sleep = "sleep"              # 睡眠
    stress = "stress"            # 压力
    metabolism = "metabolism"     # 代谢
    tcm = "tcm"                  # 中医养生


class TTMStage(str, Enum):
    """TTM 变化阶段"""
    s0 = "s0_authorization"     # 授权期
    s1 = "s1_awareness"         # 觉察期
    s2 = "s2_trial"             # 尝试期
    s3 = "s3_pathway"           # 路径期
    s4 = "s4_internalization"   # 内化期
    s5 = "s5_graduation"        # 毕业期


class AgencyMode(str, Enum):
    passive = "passive"
    transitional = "transitional"
    active = "active"


class RxDeliveryMode(str, Enum):
    """Rx 交付方式 (由 agency_mode 决定)"""
    push = "push"          # passive: 系统主动推送
    suggest = "suggest"    # transitional: 建议性推送
    available = "available"  # active: 自助可用


class RxRouteDefinition(BaseModel):
    """Rx 路由定义 (4维映射)"""
    stage: TTMStage
    domain: BPTDomain
    intensity: str  # low / medium / high
    primary_agent: str
    auxiliary_agents: List[str] = []
    delivery_modes: Dict[str, RxDeliveryMode] = {
        "passive": RxDeliveryMode.push,
        "transitional": RxDeliveryMode.suggest,
        "active": RxDeliveryMode.available,
    }
    risk_override: Optional[str] = None  # R3/R4 时的特殊路由


# ── Stage-Domain Routing Matrix (6×6=36 cells) ──
BPT6_ROUTING_MATRIX: List[RxRouteDefinition] = [
    # S0 Authorization — all gentle, push-only
    RxRouteDefinition(stage=TTMStage.s0, domain=BPTDomain.nutrition, intensity="low",
        primary_agent="journey_companion", auxiliary_agents=["nutrition"]),
    RxRouteDefinition(stage=TTMStage.s0, domain=BPTDomain.exercise, intensity="low",
        primary_agent="journey_companion", auxiliary_agents=["exercise"]),
    RxRouteDefinition(stage=TTMStage.s0, domain=BPTDomain.sleep, intensity="low",
        primary_agent="journey_companion", auxiliary_agents=["sleep"]),
    RxRouteDefinition(stage=TTMStage.s0, domain=BPTDomain.stress, intensity="low",
        primary_agent="journey_companion", auxiliary_agents=["emotion"]),
    RxRouteDefinition(stage=TTMStage.s0, domain=BPTDomain.metabolism, intensity="low",
        primary_agent="journey_companion", auxiliary_agents=["metabolic"]),
    RxRouteDefinition(stage=TTMStage.s0, domain=BPTDomain.tcm, intensity="low",
        primary_agent="journey_companion", auxiliary_agents=["tcm"]),

    # S1 Awareness — exploratory
    RxRouteDefinition(stage=TTMStage.s1, domain=BPTDomain.nutrition, intensity="low",
        primary_agent="nutrition", auxiliary_agents=["journey_companion"]),
    RxRouteDefinition(stage=TTMStage.s1, domain=BPTDomain.exercise, intensity="low",
        primary_agent="exercise", auxiliary_agents=["journey_companion"]),
    RxRouteDefinition(stage=TTMStage.s1, domain=BPTDomain.sleep, intensity="low",
        primary_agent="sleep", auxiliary_agents=["journey_companion"]),
    RxRouteDefinition(stage=TTMStage.s1, domain=BPTDomain.stress, intensity="low",
        primary_agent="emotion", auxiliary_agents=["motivation"]),
    RxRouteDefinition(stage=TTMStage.s1, domain=BPTDomain.metabolism, intensity="medium",
        primary_agent="metabolic", auxiliary_agents=["nutrition"]),
    RxRouteDefinition(stage=TTMStage.s1, domain=BPTDomain.tcm, intensity="low",
        primary_agent="tcm", auxiliary_agents=["journey_companion"]),

    # S2 Trial — medium intensity
    RxRouteDefinition(stage=TTMStage.s2, domain=BPTDomain.nutrition, intensity="medium",
        primary_agent="nutrition", auxiliary_agents=["behavior_rx", "metabolic"]),
    RxRouteDefinition(stage=TTMStage.s2, domain=BPTDomain.exercise, intensity="medium",
        primary_agent="exercise", auxiliary_agents=["behavior_rx", "cardiac_rehab"]),
    RxRouteDefinition(stage=TTMStage.s2, domain=BPTDomain.sleep, intensity="medium",
        primary_agent="sleep", auxiliary_agents=["emotion"]),
    RxRouteDefinition(stage=TTMStage.s2, domain=BPTDomain.stress, intensity="medium",
        primary_agent="emotion", auxiliary_agents=["motivation", "growth_reflection"]),
    RxRouteDefinition(stage=TTMStage.s2, domain=BPTDomain.metabolism, intensity="medium",
        primary_agent="metabolic", auxiliary_agents=["nutrition", "weight"]),
    RxRouteDefinition(stage=TTMStage.s2, domain=BPTDomain.tcm, intensity="medium",
        primary_agent="tcm", auxiliary_agents=["nutrition"]),

    # S3 Pathway — high engagement
    RxRouteDefinition(stage=TTMStage.s3, domain=BPTDomain.nutrition, intensity="high",
        primary_agent="behavior_rx", auxiliary_agents=["nutrition", "growth_reflection"]),
    RxRouteDefinition(stage=TTMStage.s3, domain=BPTDomain.exercise, intensity="high",
        primary_agent="behavior_rx", auxiliary_agents=["exercise", "cardiac_rehab"]),
    RxRouteDefinition(stage=TTMStage.s3, domain=BPTDomain.sleep, intensity="high",
        primary_agent="sleep", auxiliary_agents=["behavior_rx", "emotion"]),
    RxRouteDefinition(stage=TTMStage.s3, domain=BPTDomain.stress, intensity="high",
        primary_agent="emotion", auxiliary_agents=["growth_reflection", "coach_copilot"]),
    RxRouteDefinition(stage=TTMStage.s3, domain=BPTDomain.metabolism, intensity="high",
        primary_agent="metabolic", auxiliary_agents=["behavior_rx", "weight"]),
    RxRouteDefinition(stage=TTMStage.s3, domain=BPTDomain.tcm, intensity="medium",
        primary_agent="tcm", auxiliary_agents=["behavior_rx"]),

    # S4 Internalization — maintenance
    RxRouteDefinition(stage=TTMStage.s4, domain=BPTDomain.nutrition, intensity="medium",
        primary_agent="life_designer", auxiliary_agents=["nutrition", "growth_reflection"]),
    RxRouteDefinition(stage=TTMStage.s4, domain=BPTDomain.exercise, intensity="medium",
        primary_agent="life_designer", auxiliary_agents=["exercise"]),
    RxRouteDefinition(stage=TTMStage.s4, domain=BPTDomain.sleep, intensity="medium",
        primary_agent="life_designer", auxiliary_agents=["sleep"]),
    RxRouteDefinition(stage=TTMStage.s4, domain=BPTDomain.stress, intensity="medium",
        primary_agent="life_designer", auxiliary_agents=["emotion", "growth_reflection"]),
    RxRouteDefinition(stage=TTMStage.s4, domain=BPTDomain.metabolism, intensity="medium",
        primary_agent="life_designer", auxiliary_agents=["metabolic"]),
    RxRouteDefinition(stage=TTMStage.s4, domain=BPTDomain.tcm, intensity="low",
        primary_agent="life_designer", auxiliary_agents=["tcm"]),

    # S5 Graduation — self-directed
    RxRouteDefinition(stage=TTMStage.s5, domain=BPTDomain.nutrition, intensity="low",
        primary_agent="life_designer", auxiliary_agents=[]),
    RxRouteDefinition(stage=TTMStage.s5, domain=BPTDomain.exercise, intensity="low",
        primary_agent="life_designer", auxiliary_agents=[]),
    RxRouteDefinition(stage=TTMStage.s5, domain=BPTDomain.sleep, intensity="low",
        primary_agent="life_designer", auxiliary_agents=[]),
    RxRouteDefinition(stage=TTMStage.s5, domain=BPTDomain.stress, intensity="low",
        primary_agent="life_designer", auxiliary_agents=[]),
    RxRouteDefinition(stage=TTMStage.s5, domain=BPTDomain.metabolism, intensity="low",
        primary_agent="life_designer", auxiliary_agents=[]),
    RxRouteDefinition(stage=TTMStage.s5, domain=BPTDomain.tcm, intensity="low",
        primary_agent="life_designer", auxiliary_agents=[]),
]
