"""
rx_context_adapter.py — BehavioralProfile ORM → RxContext 适配器

将 SQLAlchemy BehavioralProfile 模型转为 BehaviorRx 引擎所需的 RxContext DTO。
安全降级: 每个字段缺失时用合理默认值。
"""
import uuid
import logging
from typing import Optional

from core.models import BehavioralProfile
from behavior_rx.core.rx_schemas import (
    RxContext, BigFiveProfile, ExpertAgentType,
)

logger = logging.getLogger(__name__)

# BehavioralStage enum → TTM int (S0=0 .. S6=6)
_STAGE_INT_MAP = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}

# StageStability enum → float
_STABILITY_MAP = {"STABLE": 0.9, "SEMI_STABLE": 0.5, "UNSTABLE": 0.2}

# primary_domain → ExpertAgentType
DOMAIN_AGENT_MAP = {
    "metabolic": ExpertAgentType.METABOLIC_EXPERT,
    "glucose": ExpertAgentType.METABOLIC_EXPERT,
    "nutrition": ExpertAgentType.BEHAVIOR_COACH,
    "exercise": ExpertAgentType.BEHAVIOR_COACH,
    "sleep": ExpertAgentType.BEHAVIOR_COACH,
    "emotion": ExpertAgentType.BEHAVIOR_COACH,
    "cardiac": ExpertAgentType.CARDIAC_EXPERT,
    "cardiac_rehab": ExpertAgentType.CARDIAC_EXPERT,
}


def profile_to_rx_context(profile: BehavioralProfile) -> RxContext:
    """
    将 BehavioralProfile ORM 对象转为 RxContext DTO。

    缺失字段一律安全降级为合理默认值。
    """
    # --- TTM Stage ---
    stage_val = 0
    if profile.current_stage:
        stage_str = profile.current_stage.value if hasattr(profile.current_stage, "value") else str(profile.current_stage)
        stage_val = _STAGE_INT_MAP.get(stage_str, 0)

    # --- Stage stability ---
    stability = 0.5
    if profile.stage_stability:
        stab_str = profile.stage_stability.value if hasattr(profile.stage_stability, "value") else str(profile.stage_stability)
        stability = _STABILITY_MAP.get(stab_str, 0.5)

    # --- BigFive ---
    big5_raw = profile.big5_scores or {}
    personality = BigFiveProfile(
        O=float(big5_raw.get("O", 50)),
        C=float(big5_raw.get("C", 50)),
        E=float(big5_raw.get("E", 50)),
        A=float(big5_raw.get("A", 50)),
        N=float(big5_raw.get("N", 50)),
    )

    # --- CAPACITY score (0-1) ---
    capacity = 0.5
    if profile.capacity_total is not None:
        # capacity_total is 0-100 in DB
        capacity = min(max(profile.capacity_total / 100.0, 0.0), 1.0)

    # --- Self-efficacy (derived from SPI) ---
    self_efficacy = 0.5
    if profile.spi_score is not None:
        self_efficacy = min(max(profile.spi_score / 100.0, 0.0), 1.0)

    # --- Barriers ---
    barriers = []
    weak = profile.capacity_weak or []
    for w in weak:
        # e.g. "A2_资源" → "resource", "T_时间" → "time"
        if "动机" in str(w) or "M_" in str(w):
            barriers.append("low_motivation")
        elif "时间" in str(w) or "T_" in str(w):
            barriers.append("forgetfulness")
        elif "信心" in str(w) or "C_" in str(w):
            barriers.append("fear")
        elif "资源" in str(w) or "A2_" in str(w):
            barriers.append("economic")
        elif "认知" in str(w):
            barriers.append("cognitive")

    # --- Risk level ---
    risk = "normal"
    risk_flags = profile.risk_flags or []
    if "dropout_risk" in risk_flags or "relapse_risk" in risk_flags:
        risk = "elevated"

    # --- Domain data ---
    domain_data = profile.domain_details or {}

    # --- user_id int → UUID ---
    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"bhp-user-{profile.user_id}")

    return RxContext(
        user_id=user_uuid,
        ttm_stage=stage_val,
        stage_readiness=profile.stage_confidence or 0.5,
        stage_stability=stability,
        personality=personality,
        capacity_score=capacity,
        self_efficacy=self_efficacy,
        domain_data=domain_data,
        active_barriers=barriers,
        recent_adherence=0.5,  # 无历史数据时取中间值
        risk_level=risk,
    )


def select_agent_type(profile: BehavioralProfile) -> ExpertAgentType:
    """基于 BehavioralProfile.primary_domains 选择最匹配的 ExpertAgentType。"""
    domains = profile.primary_domains or []
    for d in domains:
        if d in DOMAIN_AGENT_MAP:
            return DOMAIN_AGENT_MAP[d]
    return ExpertAgentType.BEHAVIOR_COACH
