"""
BehaviorOS — 行为处方基座 数据模型 (migration_031)
===================================================
3 张新表:
  1. rx_prescriptions       — 行为处方记录
  2. rx_strategy_templates  — 行为策略模板库
  3. agent_handoff_log      — Agent 交接日志

对齐 v31 models.py 惯例:
  - UUID 主键, server_default=text("gen_random_uuid()")
  - created_at / updated_at 时间戳
  - JSONB 存储灵活结构
  - 枚举使用 Python Enum + SQLAlchemy Enum
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

# ---- 假设 v31 已有的 Base & 公共引用 ----
# 实际项目中: from core.database import Base
# 此处自包含定义，部署时替换为项目 Base
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """项目 Base — 部署时替换为 core.database.Base"""
    pass


# =====================================================================
# 枚举定义
# =====================================================================

class RxStrategyType(str, enum.Enum):
    """12 种行为处方策略 (TTM 体系)"""
    CONSCIOUSNESS_RAISING = "consciousness_raising"          # 意识提升
    DRAMATIC_RELIEF = "dramatic_relief"                      # 情绪唤醒
    SELF_REEVALUATION = "self_reevaluation"                  # 自我再评价
    DECISIONAL_BALANCE = "decisional_balance"                # 决策平衡
    COGNITIVE_RESTRUCTURING = "cognitive_restructuring"      # 认知重构
    SELF_LIBERATION = "self_liberation"                      # 自我解放
    STIMULUS_CONTROL = "stimulus_control"                    # 刺激控制
    CONTINGENCY_MANAGEMENT = "contingency_management"        # 强化管理
    HABIT_STACKING = "habit_stacking"                        # 习惯叠加
    SYSTEMATIC_DESENSITIZATION = "systematic_desensitization"  # 系统脱敏
    RELAPSE_PREVENTION = "relapse_prevention"                # 复发预防
    SELF_MONITORING = "self_monitoring"                      # 自我监测


class RxIntensity(str, enum.Enum):
    """处方强度等级"""
    MINIMAL = "minimal"        # 最小干预 (观察期)
    LOW = "low"                # 低强度 (S0-S1)
    MODERATE = "moderate"      # 中等强度 (S2-S3)
    HIGH = "high"              # 高强度 (S3-S4)
    INTENSIVE = "intensive"    # 密集干预 (危机/复发)


class CommunicationStyle(str, enum.Enum):
    """沟通风格 (基于 BigFive 人格适配)"""
    EMPATHETIC = "empathetic"          # 高神经质 → 共情温暖
    DATA_DRIVEN = "data_driven"        # 高尽责性 → 数据驱动
    EXPLORATORY = "exploratory"        # 高开放性 → 探索引导
    SOCIAL_PROOF = "social_proof"      # 高宜人性 → 社会认同
    CHALLENGE = "challenge"            # 高外向性 → 挑战激励
    NEUTRAL = "neutral"                # 平衡型 → 中性专业


class HandoffType(str, enum.Enum):
    """Agent 交接类型"""
    STAGE_PROMOTION = "stage_promotion"        # 阶段提升 → 转入领域Agent
    STAGE_REGRESSION = "stage_regression"      # 阶段回退 → 回教练Agent
    DOMAIN_COORDINATION = "domain_coordination"  # 领域协同 (并行)
    CROSS_CUTTING = "cross_cutting"            # 横切面触发 (依从性)
    EMERGENCY_TAKEOVER = "emergency_takeover"  # 紧急接管
    SCHEDULED_HANDOFF = "scheduled_handoff"    # 计划交接


class HandoffStatus(str, enum.Enum):
    """交接状态"""
    INITIATED = "initiated"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ExpertAgentType(str, enum.Enum):
    """4 款专家 Agent 类型"""
    BEHAVIOR_COACH = "behavior_coach"          # 行为阶段教练
    METABOLIC_EXPERT = "metabolic_expert"      # 代谢内分泌
    CARDIAC_EXPERT = "cardiac_expert"          # 心血管康复
    ADHERENCE_EXPERT = "adherence_expert"      # 就医依从性


# =====================================================================
# 表 1: rx_prescriptions — 行为处方记录
# =====================================================================

class RxPrescription(Base):
    """
    行为处方记录表 — BehaviorRxEngine.compute_rx() 的持久化输出

    每次 Expert Agent 交互都生成一条 RxPrescription,
    记录三维计算 (TTM阶段 × BigFive人格 × CAPACITY能力) 的完整结果。
    """
    __tablename__ = "rx_prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # ---- 关联 ----
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    agent_type = Column(Enum(ExpertAgentType), nullable=False, index=True)

    # ---- 三维输入 ----
    ttm_stage = Column(Integer, nullable=False, comment="TTM阶段 S0-S6")
    bigfive_profile = Column(JSONB, nullable=False, default=dict,
                             comment="BigFive五因子分数 {O,C,E,A,N: 0-100}")
    capacity_score = Column(Float, nullable=False, default=0.5,
                            comment="CAPACITY综合能力分 0-1")

    # ---- 处方输出 ----
    goal_behavior = Column(Text, nullable=False,
                           comment="目标行为描述")
    strategy_type = Column(Enum(RxStrategyType), nullable=False,
                           comment="主策略类型")
    secondary_strategies = Column(JSONB, nullable=True, default=list,
                                  comment="辅助策略列表")
    intensity = Column(Enum(RxIntensity), nullable=False,
                       comment="处方强度")
    pace = Column(String(32), nullable=False, default="standard",
                  comment="推进节奏: slow/standard/fast/adaptive")
    communication_style = Column(Enum(CommunicationStyle), nullable=False,
                                 comment="沟通风格")

    # ---- 微行动 & 执行参数 ----
    micro_actions = Column(JSONB, nullable=False, default=list,
                           comment="微行动列表 [{action, difficulty, trigger, duration_min}]")
    reward_triggers = Column(JSONB, nullable=False, default=list,
                             comment="奖励触发条件 [{condition, reward_type, message}]")
    resistance_threshold = Column(Float, nullable=False, default=0.3,
                                  comment="阻力阈值 0-1, 超过则切换策略")
    escalation_rules = Column(JSONB, nullable=False, default=list,
                              comment="升级规则 [{condition, action, target_agent}]")

    # ---- 领域包装 ----
    domain_context = Column(JSONB, nullable=True, default=dict,
                            comment="领域特定上下文 (代谢/心血管/依从性 专有字段)")

    # ---- 效果追踪 ----
    effectiveness_score = Column(Float, nullable=True,
                                 comment="处方有效性评分 IES 0-1")
    adherence_index = Column(Float, nullable=True,
                             comment="执行依从指数 0-1")
    outcome_label = Column(String(32), nullable=True,
                           comment="结果标签: effective/partial/ineffective/pending")

    # ---- 元数据 ----
    is_active = Column(Boolean, nullable=False, default=True)
    superseded_by = Column(UUID(as_uuid=True), nullable=True,
                           comment="被替代的处方 ID (处方迭代链)")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"),
                        onupdate=datetime.utcnow)

    def __repr__(self):
        return (f"<RxPrescription {self.id} user={self.user_id} "
                f"agent={self.agent_type} stage=S{self.ttm_stage} "
                f"strategy={self.strategy_type}>")


# =====================================================================
# 表 2: rx_strategy_templates — 行为策略模板库
# =====================================================================

class RxStrategyTemplate(Base):
    """
    行为策略模板库 — 12 种策略 × 4 域 × 7 阶段 的预配置模板

    每个模板定义了一种策略在特定领域/阶段下的标准参数,
    BehaviorRxEngine 根据三维计算结果从模板库中选取并个性化。
    """
    __tablename__ = "rx_strategy_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # ---- 定位维度 ----
    strategy_type = Column(Enum(RxStrategyType), nullable=False, index=True)
    domain = Column(String(32), nullable=False, default="general", index=True,
                    comment="适用领域: general/metabolic/cardiac/adherence")
    ttm_stage_min = Column(Integer, nullable=False, default=0,
                           comment="最小适用阶段 S0-S6")
    ttm_stage_max = Column(Integer, nullable=False, default=6,
                           comment="最大适用阶段 S0-S6")

    # ---- 模板内容 ----
    name = Column(String(128), nullable=False)
    name_zh = Column(String(128), nullable=False, comment="中文名称")
    description = Column(Text, nullable=True)
    core_mechanism = Column(Text, nullable=False,
                            comment="核心作用机制描述")
    typical_applications = Column(JSONB, nullable=False, default=list,
                                  comment="典型应用场景 [str]")

    # ---- 默认参数 ----
    default_intensity = Column(Enum(RxIntensity), nullable=False, default=RxIntensity.MODERATE)
    default_pace = Column(String(32), nullable=False, default="standard")
    default_micro_actions = Column(JSONB, nullable=False, default=list,
                                   comment="默认微行动模板")
    default_reward_triggers = Column(JSONB, nullable=False, default=list)
    default_resistance_threshold = Column(Float, nullable=False, default=0.3)

    # ---- 人格适配 ----
    personality_modifiers = Column(JSONB, nullable=False, default=dict,
                                   comment="人格调节参数 {high_N: {}, high_C: {}, ...}")

    # ---- 管理 ----
    evidence_tier = Column(String(8), nullable=False, default="T2",
                           comment="证据等级 T1-T4")
    is_enabled = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"),
                        onupdate=datetime.utcnow)

    def __repr__(self):
        return (f"<RxStrategyTemplate {self.strategy_type.value} "
                f"domain={self.domain} S{self.ttm_stage_min}-S{self.ttm_stage_max}>")


# =====================================================================
# 表 3: agent_handoff_log — Agent 交接日志
# =====================================================================

class AgentHandoffLog(Base):
    """
    Agent 交接日志 — 记录 4 款 Expert Agent 之间的交接事件

    交接场景:
      - 阶段提升: BehaviorCoach → MetabolicExpert (S2→S3)
      - 阶段回退: MetabolicExpert → BehaviorCoach (S3→S1)
      - 横切面: 任意Agent → AdherenceExpert (服药缺失)
      - 紧急接管: 任意Agent → BehaviorCoach (自我效能崩塌)
    """
    __tablename__ = "agent_handoff_log"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # ---- 关联 ----
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)

    # ---- 交接方 ----
    from_agent = Column(Enum(ExpertAgentType), nullable=False, index=True)
    to_agent = Column(Enum(ExpertAgentType), nullable=False, index=True)
    handoff_type = Column(Enum(HandoffType), nullable=False, index=True)
    status = Column(Enum(HandoffStatus), nullable=False, default=HandoffStatus.INITIATED)

    # ---- 交接上下文 ----
    rx_context = Column(JSONB, nullable=False, default=dict,
                        comment="处方上下文 {stage, readiness, personality_profile, capacity_score}")
    rx_prescription_id = Column(UUID(as_uuid=True), nullable=True,
                                comment="关联的处方 ID")

    # ---- 触发条件 ----
    trigger_reason = Column(Text, nullable=False,
                            comment="交接触发原因")
    trigger_data = Column(JSONB, nullable=True, default=dict,
                          comment="触发数据 {metric_name, value, threshold}")

    # ---- 结果 ----
    outcome = Column(JSONB, nullable=True, default=dict,
                     comment="交接结果 {ies_score, adherence_index, stage_change}")
    resolution_notes = Column(Text, nullable=True)

    # ---- 时间戳 ----
    initiated_at = Column(DateTime, nullable=False, server_default=text("now()"))
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))

    def __repr__(self):
        return (f"<AgentHandoff {self.from_agent.value}→{self.to_agent.value} "
                f"type={self.handoff_type.value} status={self.status.value}>")
