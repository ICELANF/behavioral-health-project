"""
BehaviorOS — 行为处方 Pydantic Schemas
=======================================
RxPrescription DTO 及 API 请求/响应模型

核心对象:
  RxPrescriptionDTO — BehaviorRxEngine.compute_rx() 的计算结果对象
  RxContext         — 三维输入上下文
  HandoffRequest    — Agent 交接请求
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =====================================================================
# 枚举 (镜像 ORM 枚举, 用于 Pydantic 校验)
# =====================================================================

class RxStrategyType(str, Enum):
    CONSCIOUSNESS_RAISING = "consciousness_raising"
    DRAMATIC_RELIEF = "dramatic_relief"
    SELF_REEVALUATION = "self_reevaluation"
    DECISIONAL_BALANCE = "decisional_balance"
    COGNITIVE_RESTRUCTURING = "cognitive_restructuring"
    SELF_LIBERATION = "self_liberation"
    STIMULUS_CONTROL = "stimulus_control"
    CONTINGENCY_MANAGEMENT = "contingency_management"
    HABIT_STACKING = "habit_stacking"
    SYSTEMATIC_DESENSITIZATION = "systematic_desensitization"
    RELAPSE_PREVENTION = "relapse_prevention"
    SELF_MONITORING = "self_monitoring"


class RxIntensity(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    INTENSIVE = "intensive"


class CommunicationStyle(str, Enum):
    EMPATHETIC = "empathetic"
    DATA_DRIVEN = "data_driven"
    EXPLORATORY = "exploratory"
    SOCIAL_PROOF = "social_proof"
    CHALLENGE = "challenge"
    NEUTRAL = "neutral"


class ExpertAgentType(str, Enum):
    BEHAVIOR_COACH = "behavior_coach"
    METABOLIC_EXPERT = "metabolic_expert"
    CARDIAC_EXPERT = "cardiac_expert"
    ADHERENCE_EXPERT = "adherence_expert"


class HandoffType(str, Enum):
    STAGE_PROMOTION = "stage_promotion"
    STAGE_REGRESSION = "stage_regression"
    DOMAIN_COORDINATION = "domain_coordination"
    CROSS_CUTTING = "cross_cutting"
    EMERGENCY_TAKEOVER = "emergency_takeover"
    SCHEDULED_HANDOFF = "scheduled_handoff"


class HandoffStatus(str, Enum):
    INITIATED = "initiated"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# =====================================================================
# 核心 DTO: BigFive 人格维度
# =====================================================================

class BigFiveProfile(BaseModel):
    """BigFive 五因子人格剖面 (0-100)"""
    O: float = Field(50.0, ge=0, le=100, description="开放性 Openness")
    C: float = Field(50.0, ge=0, le=100, description="尽责性 Conscientiousness")
    E: float = Field(50.0, ge=0, le=100, description="外向性 Extraversion")
    A: float = Field(50.0, ge=0, le=100, description="宜人性 Agreeableness")
    N: float = Field(50.0, ge=0, le=100, description="神经质 Neuroticism")

    def dominant_trait(self) -> str:
        """返回最显著的人格特质"""
        traits = {"O": self.O, "C": self.C, "E": self.E, "A": self.A, "N": self.N}
        return max(traits, key=traits.get)

    def is_high(self, trait: str, threshold: float = 65.0) -> bool:
        return getattr(self, trait, 50.0) >= threshold

    def is_low(self, trait: str, threshold: float = 35.0) -> bool:
        return getattr(self, trait, 50.0) <= threshold


# =====================================================================
# 核心 DTO: 三维输入上下文
# =====================================================================

class RxContext(BaseModel):
    """
    行为处方三维输入上下文

    三维:
      1. TTM 阶段 (S0-S6) — 行为改变准备度
      2. BigFive 人格 — 沟通风格 & 策略适配
      3. CAPACITY 能力 — 执行难度校准
    """
    user_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None

    # 维度 1: TTM 阶段
    ttm_stage: int = Field(..., ge=0, le=6, description="TTM阶段 0=前意识 6=终止")
    stage_readiness: float = Field(0.5, ge=0, le=1, description="阶段就绪度")
    stage_stability: float = Field(0.5, ge=0, le=1, description="阶段稳定度")

    # 维度 2: 人格
    personality: BigFiveProfile = Field(default_factory=BigFiveProfile)

    # 维度 3: 能力
    capacity_score: float = Field(0.5, ge=0, le=1, description="CAPACITY综合能力分")
    self_efficacy: float = Field(0.5, ge=0, le=1, description="自我效能感")

    # 附加上下文
    domain_data: Dict[str, Any] = Field(default_factory=dict,
                                        description="领域特定数据")
    active_barriers: List[str] = Field(default_factory=list,
                                       description="当前活跃障碍列表")
    recent_adherence: float = Field(0.5, ge=0, le=1,
                                    description="近期依从率")
    risk_level: str = Field("normal", description="风险级别: low/normal/elevated/high/critical")


# =====================================================================
# 核心 DTO: 微行动
# =====================================================================

class MicroAction(BaseModel):
    """微行动定义"""
    action: str = Field(..., description="行动描述")
    difficulty: float = Field(0.3, ge=0, le=1, description="难度 0-1")
    trigger: str = Field("", description="触发场景")
    duration_min: int = Field(5, ge=1, description="预估分钟数")
    frequency: str = Field("daily", description="频率: daily/weekly/on_trigger")
    domain: str = Field("general", description="所属领域")


class RewardTrigger(BaseModel):
    """奖励触发器"""
    condition: str = Field(..., description="触发条件描述")
    reward_type: str = Field("praise", description="奖励类型: praise/badge/points/milestone")
    message: str = Field("", description="奖励消息模板")


class EscalationRule(BaseModel):
    """升级规则"""
    condition: str = Field(..., description="触发条件")
    action: str = Field(..., description="升级动作: switch_strategy/handoff/alert_coach")
    target_agent: Optional[ExpertAgentType] = None
    priority: int = Field(5, ge=1, le=10, description="优先级 1-10")


# =====================================================================
# 核心 DTO: RxPrescription — 处方计算结果
# =====================================================================

class RxPrescriptionDTO(BaseModel):
    """
    行为处方计算结果 — BehaviorRxEngine.compute_rx() 的输出

    包含 12 个字段的完整处方对象:
      目标行为 + 主策略 + 辅助策略 + 强度 + 节奏 + 沟通风格
      + 微行动 + 奖励触发 + 阻力阈值 + 升级规则 + 领域上下文 + 处方ID
    """
    # ---- 标识 ----
    rx_id: Optional[uuid.UUID] = None
    agent_type: ExpertAgentType

    # ---- 处方核心 (6 字段) ----
    goal_behavior: str = Field(..., description="目标行为描述")
    strategy_type: RxStrategyType = Field(..., description="主策略类型")
    secondary_strategies: List[RxStrategyType] = Field(
        default_factory=list, description="辅助策略")
    intensity: RxIntensity = Field(..., description="处方强度")
    pace: str = Field("standard", description="推进节奏")
    communication_style: CommunicationStyle = Field(..., description="沟通风格")

    # ---- 执行参数 (4 字段) ----
    micro_actions: List[MicroAction] = Field(default_factory=list)
    reward_triggers: List[RewardTrigger] = Field(default_factory=list)
    resistance_threshold: float = Field(0.3, ge=0, le=1)
    escalation_rules: List[EscalationRule] = Field(default_factory=list)

    # ---- 领域上下文 (1 字段) ----
    domain_context: Dict[str, Any] = Field(default_factory=dict)

    # ---- 元数据 ----
    ttm_stage: int = Field(..., ge=0, le=6)
    confidence: float = Field(0.8, ge=0, le=1, description="处方置信度")
    reasoning: str = Field("", description="处方推理说明")

    class Config:
        json_encoders = {uuid.UUID: str}


# =====================================================================
# 交接相关 DTO
# =====================================================================

class HandoffContext(BaseModel):
    """交接上下文"""
    stage: int = Field(..., ge=0, le=6)
    readiness: float = Field(0.5, ge=0, le=1)
    personality_profile: BigFiveProfile = Field(default_factory=BigFiveProfile)
    capacity_score: float = Field(0.5, ge=0, le=1)
    active_rx_id: Optional[uuid.UUID] = None
    domain_state: Dict[str, Any] = Field(default_factory=dict)


class HandoffRequest(BaseModel):
    """Agent 交接请求"""
    user_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    from_agent: ExpertAgentType
    to_agent: ExpertAgentType
    handoff_type: HandoffType
    trigger_reason: str
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    rx_context: HandoffContext
    rx_prescription_id: Optional[uuid.UUID] = None


class HandoffResponse(BaseModel):
    """Agent 交接响应"""
    handoff_id: uuid.UUID
    status: HandoffStatus
    accepted: bool
    message: str = ""
    new_rx: Optional[RxPrescriptionDTO] = None


# =====================================================================
# API 请求/响应模型
# =====================================================================

class ComputeRxRequest(BaseModel):
    """计算行为处方 API 请求"""
    context: RxContext
    agent_type: ExpertAgentType
    override_strategy: Optional[RxStrategyType] = None
    override_intensity: Optional[RxIntensity] = None


class ComputeRxResponse(BaseModel):
    """计算行为处方 API 响应"""
    prescription: RxPrescriptionDTO
    persisted: bool = False
    rx_id: Optional[uuid.UUID] = None


class RxListResponse(BaseModel):
    """处方列表响应"""
    items: List[RxPrescriptionDTO]
    total: int
    page: int = 1
    page_size: int = 20


class StrategyTemplateResponse(BaseModel):
    """策略模板响应"""
    id: uuid.UUID
    strategy_type: RxStrategyType
    domain: str
    name: str
    name_zh: str
    ttm_stage_min: int
    ttm_stage_max: int
    default_intensity: RxIntensity
    evidence_tier: str
    is_enabled: bool


class HandoffListResponse(BaseModel):
    """交接日志列表响应"""
    items: List[Dict[str, Any]]
    total: int
