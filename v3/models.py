"""
BHP v3.1 新增数据模型 — 追加到 api/models.py
"""
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, JSON,
    ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.sql import func

from v3.database import Base


class ChangeCauseCategory(str, PyEnum):
    INTRINSIC = "intrinsic"
    EXTERNAL_EVENT = "external_event"
    EMOTIONAL = "emotional"
    COGNITIVE = "cognitive"
    CAPABILITY = "capability"
    SOCIAL = "social"

class HealthCompetencyLevel(str, PyEnum):
    LV0 = "Lv0"; LV1 = "Lv1"; LV2 = "Lv2"
    LV3 = "Lv3"; LV4 = "Lv4"; LV5 = "Lv5"

class ObstacleCategory(str, PyEnum):
    TIME = "time"; ENERGY = "energy"; KNOWLEDGE = "knowledge"
    SKILL = "skill"; ENVIRONMENT = "environment"; SOCIAL = "social"
    EMOTION = "emotion"; FINANCIAL = "financial"; HABIT = "habit"
    BELIEF = "belief"

class HBMDimension(str, PyEnum):
    SUSCEPTIBILITY = "susceptibility"; SEVERITY = "severity"
    BENEFITS = "benefits"; BARRIERS = "barriers"
    CUES = "cues"; SELF_EFFICACY = "self_efficacy"

class AttributionType(str, PyEnum):
    BEHAVIORAL = "behavioral"; GENETIC = "genetic"
    ENVIRONMENTAL = "environmental"; FATALISTIC = "fatalistic"

class TimeOrientation(str, PyEnum):
    PAST = "past"; PRESENT = "present"; FUTURE = "future"

class SupportLayer(str, PyEnum):
    CORE = "core"; INTIMATE = "intimate"; DAILY = "daily"
    PROFESSIONAL = "professional"; COMMUNITY = "community"

class MonitoringLevel(str, PyEnum):
    DAILY = "daily"; WEEKLY = "weekly"; MONTHLY = "monthly"


# ── 表 ───────────────────────────────────────────

class ChangeCause(Base):
    __tablename__ = "change_causes"
    id = Column(String(4), primary_key=True)
    category = Column(String(20), nullable=False)
    name_zh = Column(String(50), nullable=False)
    name_en = Column(String(50), nullable=False)
    description = Column(Text)
    assessment_question = Column(Text, nullable=False)
    weight = Column(Float, default=1.0)

class UserChangeCauseScore(Base):
    __tablename__ = "user_change_cause_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, nullable=False)
    cause_id = Column(String(4), ForeignKey("change_causes.id"), nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index("ix_user_cause_ua", "user_id", "assessment_id"),)

class InterventionStrategy(Base):
    __tablename__ = "intervention_strategies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_code = Column(String(4), nullable=False, index=True)
    readiness_level = Column(String(4), index=True)
    stage_name = Column(String(20), nullable=False)
    cause_code = Column(String(4), nullable=False, index=True)
    cause_category = Column(String(30), nullable=False)
    cause_name = Column(String(30), nullable=False)
    strategy_type = Column(String(30), nullable=False)
    coach_script = Column(Text, nullable=False)
    __table_args__ = (
        UniqueConstraint("stage_code", "cause_code", name="uq_stage_cause"),
        Index("ix_strat_rc", "readiness_level", "cause_code"),
    )

class HealthCompetencyAssessment(Base):
    __tablename__ = "health_competency_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    level_scores = Column(JSON, nullable=False)
    current_level = Column(String(4), nullable=False)
    recommended_content_stage = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())

class COMBAssessment(Base):
    __tablename__ = "comb_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    dimension_scores = Column(JSON, nullable=False)
    bottleneck = Column(String(20))
    total_score = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class SelfEfficacyAssessment(Base):
    __tablename__ = "self_efficacy_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    avg_score = Column(Float, nullable=False)
    level = Column(String(10), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class ObstacleAssessment(Base):
    __tablename__ = "obstacle_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    category_scores = Column(JSON, nullable=False)
    top_obstacles = Column(JSON, nullable=False)
    rx_adjustments = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

class SupportAssessment(Base):
    __tablename__ = "support_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    layer_scores = Column(JSON, nullable=False)
    total_score = Column(Float, nullable=False)
    support_level = Column(String(10), nullable=False)
    weakest_layer = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
