"""
Bridge: models.knowledge → core.models (Knowledge* 模型)

为测试套件提供预期的导入路径：
  from models.knowledge import KnowledgeDocument, KnowledgeChunk, ...
"""
import sys, os

# 确保项目根目录在 path (backend/ 的父目录)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.models import (
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeCitation,
)

# ── 测试需要但项目中用字符串的枚举 ──

import enum


class DocStatus(str, enum.Enum):
    """文档状态"""
    pending = "pending"
    processing = "processing"
    ready = "ready"
    error = "error"


class KnowledgeScope(str, enum.Enum):
    """知识范围"""
    platform = "platform"
    domain = "domain"
    tenant = "tenant"


# ── KnowledgeDomain 模型 (补充) ──

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# 复用项目的 Base
from core.models import Base


class KnowledgeDomain(Base):
    """知识领域元数据"""
    __tablename__ = "knowledge_domains"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(String(50), unique=True, nullable=False, index=True)
    label = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


__all__ = [
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeCitation",
    "KnowledgeDomain",
    "DocStatus",
    "KnowledgeScope",
]
