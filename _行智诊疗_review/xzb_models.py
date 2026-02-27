"""
行诊智伴 (XZB) 数据模型
- SQLAlchemy ORM 模型
- Pydantic 请求/响应模型
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, List, Optional
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, func
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field

Base = declarative_base()


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class KnowledgeType(str, Enum):
    note = "note"
    rule = "rule"
    case = "case"
    annotation = "annotation"
    template = "template"
    forbidden = "forbidden"

class EvidenceTier(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"

class ActionType(str, Enum):
    respond = "respond"
    refer = "refer"
    prescribe = "prescribe"
    warn = "warn"
    defer = "defer"

class RxStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"

class InterventionType(str, Enum):
    takeover = "takeover"
    async_reply = "async_reply"
    rx_trigger = "rx_trigger"
    knowledge_push = "knowledge_push"


# ─────────────────────────────────────────────
# ORM Models
# ─────────────────────────────────────────────

class XZBExpertProfile(Base):
    __tablename__ = "xzb_expert_profiles"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    display_name     = Column(String(100), nullable=False)
    specialty        = Column(String(200))
    license_no       = Column(String(100))
    license_verified = Column(Boolean, default=False)
    tcm_weight       = Column(Float, default=0.5)
    style_profile    = Column(JSONB, default=dict)
    domain_tags      = Column(ARRAY(Text), default=list)
    is_active        = Column(Boolean, default=True)
    last_active_at   = Column(DateTime)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    config       = relationship("XZBConfig", back_populates="expert", uselist=False)
    knowledge    = relationship("XZBKnowledge", back_populates="expert")
    rules        = relationship("XZBKnowledgeRule", back_populates="expert")
    conversations = relationship("XZBConversation", back_populates="expert")


class XZBConfig(Base):
    __tablename__ = "xzb_configs"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id        = Column(UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"), nullable=False, unique=True)
    companion_name   = Column(String(100), nullable=False)
    greeting         = Column(Text)
    comm_style       = Column(JSONB, default=dict)
    boundary_stmt    = Column(Text)
    referral_rules   = Column(JSONB, default=list)
    auto_rx_enabled  = Column(Boolean, default=True)
    dormant_mode     = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expert = relationship("XZBExpertProfile", back_populates="config")


class XZBKnowledge(Base):
    __tablename__ = "xzb_knowledge"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id             = Column(UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"), nullable=False)
    type                  = Column(String(20), nullable=False)
    content               = Column(Text, nullable=False)
    evidence_tier         = Column(String(2))
    vector_embedding      = Column(Vector(768))
    source                = Column(Text)
    tags                  = Column(ARRAY(Text), default=list)
    applicable_conditions = Column(JSONB, default=dict)
    confidence_override   = Column(Float)
    usage_count           = Column(Integer, default=0)
    expert_confirmed      = Column(Boolean, default=False)
    expires_at            = Column(DateTime)
    is_active             = Column(Boolean, default=True)
    needs_review          = Column(Boolean, default=False)
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expert = relationship("XZBExpertProfile", back_populates="knowledge")


class XZBKnowledgeRule(Base):
    __tablename__ = "xzb_knowledge_rules"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id      = Column(UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"), nullable=False)
    rule_name      = Column(String(200))
    condition_json = Column(JSONB, nullable=False)
    action_type    = Column(String(20))
    action_content = Column(Text, nullable=False)
    priority       = Column(Integer, default=50)
    overrides_llm  = Column(Boolean, default=False)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expert = relationship("XZBExpertProfile", back_populates="rules")


class XZBConversation(Base):
    __tablename__ = "xzb_conversations"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id           = Column(UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"), nullable=False)
    seeker_id           = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_ref         = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    summary             = Column(Text)
    rx_triggered        = Column(Boolean, default=False)
    expert_intervened   = Column(Boolean, default=False)
    knowledge_mined     = Column(Boolean, default=False)
    ttm_stage_at_start  = Column(String(2))
    created_at          = Column(DateTime, default=datetime.utcnow)
    ended_at            = Column(DateTime)

    expert       = relationship("XZBExpertProfile", back_populates="conversations")
    rx_fragments = relationship("XZBRxFragment", back_populates="conversation")
    interventions = relationship("XZBExpertIntervention", back_populates="conversation")


class XZBRxFragment(Base):
    __tablename__ = "xzb_rx_fragments"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id       = Column(UUID(as_uuid=True), ForeignKey("xzb_conversations.id"))
    expert_id             = Column(UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"), nullable=False)
    seeker_id             = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    source                = Column(String(50), default="xzb_expert")
    priority              = Column(Integer, default=0)
    evidence_tier         = Column(String(2))
    domain                = Column(String(100))
    strategies            = Column(JSONB, default=list)
    knowledge_refs        = Column(ARRAY(UUID(as_uuid=True)), default=list)
    style_profile_id      = Column(UUID(as_uuid=True))
    contraindications     = Column(ARRAY(Text), default=list)
    requires_coach_review = Column(Boolean, default=True)
    rx_id                 = Column(UUID(as_uuid=True))
    status                = Column(String(20), default="draft")
    created_at            = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("XZBConversation", back_populates="rx_fragments")


class XZBExpertIntervention(Base):
    __tablename__ = "xzb_expert_interventions"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id   = Column(UUID(as_uuid=True), ForeignKey("xzb_conversations.id"), nullable=False)
    expert_id         = Column(UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"), nullable=False)
    intervention_type = Column(String(20))
    content           = Column(Text)
    created_at        = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("XZBConversation", back_populates="interventions")


# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────

class ExpertRegisterRequest(BaseModel):
    display_name: str
    specialty: Optional[str] = None
    license_no: Optional[str] = None
    tcm_weight: float = Field(0.5, ge=0.0, le=1.0)
    domain_tags: List[str] = []
    companion_name: str
    greeting: Optional[str] = None
    boundary_stmt: Optional[str] = None

class ExpertProfileResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    specialty: Optional[str]
    license_verified: bool
    tcm_weight: float
    domain_tags: List[str]
    is_active: bool
    last_active_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class KnowledgeCreateRequest(BaseModel):
    type: KnowledgeType
    content: str
    evidence_tier: Optional[EvidenceTier] = None
    source: Optional[str] = None
    tags: List[str] = []
    applicable_conditions: dict = {}
    confidence_override: Optional[float] = None
    expires_at: Optional[datetime] = None

class KnowledgeResponse(BaseModel):
    id: uuid.UUID
    type: KnowledgeType
    evidence_tier: Optional[str]
    source: Optional[str]
    tags: List[str]
    usage_count: int
    expert_confirmed: bool
    needs_review: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RuleCreateRequest(BaseModel):
    rule_name: Optional[str] = None
    condition_json: dict
    action_type: ActionType
    action_content: str
    priority: int = 50
    overrides_llm: bool = False

class XZBRxFragmentSchema(BaseModel):
    """注入 RxComposer 的处方片段格式"""
    source: str = "xzb_expert"
    expert_id: uuid.UUID
    expert_name: str
    priority: int = 0
    evidence_tier: Optional[str] = None
    domain: Optional[str] = None
    strategies: List[dict] = []
    knowledge_refs: List[uuid.UUID] = []
    style_profile_id: Optional[uuid.UUID] = None
    contraindications: List[str] = []
    requires_coach_review: bool = True   # 铁律：始终为 True
