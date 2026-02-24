"""
行智诊疗 (XZB) 数据模型
- SQLAlchemy ORM 模型 (使用平台 Base)
- Pydantic 请求/响应模型

已适配:
  - UUID PK: server_default=gen_random_uuid() (平台规范)
  - Timestamp: server_default=func.now() (平台规范)
  - Base: 复用 core.models.Base (非独立 declarative_base)
  - Enum: 命名避免与平台 EvidenceTier 冲突 → XZBEvidenceTier
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, func, text as sa_text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

from core.models import Base


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


class XZBEvidenceTier(str, Enum):
    """行智诊疗证据分级 (命名避免与平台 EvidenceTier 冲突)"""
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


class PostType(str, Enum):
    """医道汇帖子类型 (与DDL CHECK约束对齐)"""
    case = "case"
    literature = "literature"
    discussion = "discussion"
    guideline = "guideline"
    tip = "tip"


class SharingPermission(str, Enum):
    """知识共享权限类型 (与DDL CHECK约束对齐)"""
    read = "read"
    adapt = "adapt"


# ─────────────────────────────────────────────
# ORM Models — 使用平台 Base, UUID server_default, func.now()
# ─────────────────────────────────────────────

class XZBExpertProfile(Base):
    """专家画像表"""
    __tablename__ = "xzb_expert_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    specialty = Column(String(200))
    license_no = Column(String(100))
    license_verified = Column(Boolean, server_default=sa_text("false"))
    tcm_weight = Column(Float, server_default=sa_text("0.5"))
    style_profile = Column(JSONB, server_default=sa_text("'{}'::jsonb"))
    domain_tags = Column(ARRAY(Text), server_default=sa_text("'{}'::text[]"))
    is_active = Column(Boolean, server_default=sa_text("true"))
    last_active_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    config = relationship("XZBConfig", back_populates="expert", uselist=False)
    knowledge = relationship("XZBKnowledge", back_populates="expert")
    rules = relationship("XZBKnowledgeRule", back_populates="expert")
    conversations = relationship("XZBConversation", back_populates="expert")


class XZBConfig(Base):
    """智伴配置表"""
    __tablename__ = "xzb_configs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    expert_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id", ondelete="CASCADE"),
                       nullable=False, unique=True)
    companion_name = Column(String(100), nullable=False)
    greeting = Column(Text)
    comm_style = Column(JSONB, server_default=sa_text("'{}'::jsonb"))
    boundary_stmt = Column(Text)
    referral_rules = Column(JSONB, server_default=sa_text("'[]'::jsonb"))
    auto_rx_enabled = Column(Boolean, server_default=sa_text("true"))
    dormant_mode = Column(Boolean, server_default=sa_text("false"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    expert = relationship("XZBExpertProfile", back_populates="config")


class XZBKnowledge(Base):
    """专家知识条目表"""
    __tablename__ = "xzb_knowledge"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    expert_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id", ondelete="CASCADE"),
                       nullable=False)
    type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    evidence_tier = Column(String(2))
    vector_embedding = Column(Vector(768)) if Vector else Column(Text)
    source = Column(Text)
    tags = Column(ARRAY(Text), server_default=sa_text("'{}'::text[]"))
    applicable_conditions = Column(JSONB, server_default=sa_text("'{}'::jsonb"))
    confidence_override = Column(Float)
    usage_count = Column(Integer, server_default=sa_text("0"))
    expert_confirmed = Column(Boolean, server_default=sa_text("false"))
    expires_at = Column(DateTime)
    is_active = Column(Boolean, server_default=sa_text("true"))
    needs_review = Column(Boolean, server_default=sa_text("false"))
    source_conversation_id = Column(PG_UUID(as_uuid=True))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    expert = relationship("XZBExpertProfile", back_populates="knowledge")


class XZBKnowledgeRule(Base):
    """诊疗规则表 (IF-THEN)"""
    __tablename__ = "xzb_knowledge_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    expert_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id", ondelete="CASCADE"),
                       nullable=False)
    rule_name = Column(String(200))
    condition_json = Column(JSONB, nullable=False)
    action_type = Column(String(20))
    action_content = Column(Text, nullable=False)
    priority = Column(Integer, server_default=sa_text("50"))
    overrides_llm = Column(Boolean, server_default=sa_text("false"))
    is_active = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    expert = relationship("XZBExpertProfile", back_populates="rules")


class XZBConversation(Base):
    """对话记录表"""
    __tablename__ = "xzb_conversations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    expert_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"),
                       nullable=False)
    seeker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_ref = Column(Integer, ForeignKey("chat_sessions.id"))
    summary = Column(Text)
    messages_json = Column(JSONB, server_default=sa_text("'[]'::jsonb"))
    rx_triggered = Column(Boolean, server_default=sa_text("false"))
    expert_intervened = Column(Boolean, server_default=sa_text("false"))
    knowledge_mined = Column(Boolean, server_default=sa_text("false"))
    ttm_stage_at_start = Column(String(2))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    ended_at = Column(DateTime)

    expert = relationship("XZBExpertProfile", back_populates="conversations")
    rx_fragments = relationship("XZBRxFragment", back_populates="conversation")
    interventions = relationship("XZBExpertIntervention", back_populates="conversation")


class XZBRxFragment(Base):
    """处方片段表 (注入RxComposer)"""
    __tablename__ = "xzb_rx_fragments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_conversations.id"))
    expert_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"),
                       nullable=False)
    seeker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source = Column(String(50), server_default=sa_text("'xzb_expert'"))
    priority = Column(Integer, server_default=sa_text("0"))
    evidence_tier = Column(String(2))
    domain = Column(String(100))
    strategies = Column(JSONB, server_default=sa_text("'[]'::jsonb"), nullable=False)
    knowledge_refs = Column(ARRAY(PG_UUID(as_uuid=True)),
                            server_default=sa_text("'{}'::uuid[]"))
    style_profile_id = Column(PG_UUID(as_uuid=True))
    contraindications = Column(ARRAY(Text), server_default=sa_text("'{}'::text[]"))
    requires_coach_review = Column(Boolean, server_default=sa_text("true"), nullable=False)
    rx_id = Column(PG_UUID(as_uuid=True))
    status = Column(String(20), server_default=sa_text("'draft'"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    conversation = relationship("XZBConversation", back_populates="rx_fragments")


class XZBExpertIntervention(Base):
    """专家介入记录表"""
    __tablename__ = "xzb_expert_interventions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    conversation_id = Column(PG_UUID(as_uuid=True),
                             ForeignKey("xzb_conversations.id"), nullable=False)
    expert_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("xzb_expert_profiles.id"), nullable=False)
    intervention_type = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    conversation = relationship("XZBConversation", back_populates="interventions")


# ── Phase 3: 医道汇 ──────────────────────────────────────

class XZBMedCircle(Base):
    """医道汇帖子表"""
    __tablename__ = "xzb_med_circle"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    author_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"),
                       nullable=False)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    post_type = Column(String(20))
    tags = Column(ARRAY(Text), server_default=sa_text("'{}'::text[]"))
    view_count = Column(Integer, server_default=sa_text("0"))
    like_count = Column(Integer, server_default=sa_text("0"))
    is_published = Column(Boolean, server_default=sa_text("false"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    comments = relationship("XZBMedCircleComment", back_populates="post")


class XZBMedCircleComment(Base):
    """医道汇评论表"""
    __tablename__ = "xzb_med_circle_comments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_med_circle.id",
                     ondelete="CASCADE"), nullable=False)
    author_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"),
                       nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("xzb_med_circle_comments.id"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    post = relationship("XZBMedCircle", back_populates="comments")


class XZBKnowledgeSharing(Base):
    """知识共享权限表"""
    __tablename__ = "xzb_knowledge_sharing"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    knowledge_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_knowledge.id"),
                          nullable=False)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"),
                      nullable=False)
    grantee_id = Column(PG_UUID(as_uuid=True), ForeignKey("xzb_expert_profiles.id"))
    permission = Column(String(20), server_default=sa_text("'read'"))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


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
    specialty: Optional[str] = None
    license_verified: bool = False
    tcm_weight: float = 0.5
    domain_tags: List[str] = []
    is_active: bool = True
    last_active_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeCreateRequest(BaseModel):
    type: KnowledgeType
    content: str
    evidence_tier: Optional[XZBEvidenceTier] = None
    source: Optional[str] = None
    tags: List[str] = []
    applicable_conditions: dict = {}
    confidence_override: Optional[float] = None
    expires_at: Optional[datetime] = None


class KnowledgeResponse(BaseModel):
    id: uuid.UUID
    type: KnowledgeType
    evidence_tier: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []
    usage_count: int = 0
    expert_confirmed: bool = False
    needs_review: bool = False
    created_at: Optional[datetime] = None

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
