"""
V4.0 Reflection Journal Service — 反思日志系统 (MEU-30)

Features:
  - Create/list/detail reflection journal entries
  - Analyze reflection depth (S4 awareness depth)
  - Link to agency_score updates
  - Supports structured and freeform entries
  - Prompts based on agency_mode
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.models import Base, User, JourneyState
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

logger = logging.getLogger(__name__)


# ── ORM Model (will be created by migration or auto) ────

class ReflectionJournal(Base):
    """反思日志"""
    __tablename__ = "reflection_journals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Content
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    journal_type = Column(String(30), default="freeform")  # freeform/guided/weekly/monthly

    # Analysis
    reflection_depth = Column(Float, default=0.0)  # 0-1 (S4 score)
    depth_level = Column(String(20), default="surface")  # surface/pattern/insight/identity
    agency_mode_at_time = Column(String(20), nullable=True)

    # Metadata
    tags = Column(JSON, default=[])
    prompt_used = Column(String(200), nullable=True)  # The reflection prompt used

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)


# ── Reflection Prompts by Agency Mode ───────────

REFLECTION_PROMPTS = {
    "passive": [
        "今天有什么让你感到意外的事?",
        "这周让你最开心的一件事是什么?",
        "你最近注意到身体有什么变化吗?",
        "有没有什么小事让你觉得'还不错'?",
    ],
    "transitional": [
        "你注意到自己有什么新的行为模式了吗?",
        "这周你做了什么和以前不一样的选择?",
        "你觉得什么在帮助你改变? 什么在阻碍你?",
        "如果你能给上周的自己一个建议, 会是什么?",
    ],
    "active": [
        "这个发现如何改变了你对自己的看法?",
        "你正在成为什么样的人? 这和以前有什么不同?",
        "你最近帮助了谁? 这给你带来了什么?",
        "回顾你的成长旅程, 有什么是你现在才理解的?",
    ],
}


class ReflectionService:
    """反思日志服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_entry(
        self,
        user_id: int,
        content: str,
        title: str = None,
        journal_type: str = "freeform",
        tags: list = None,
        prompt_used: str = None,
    ) -> dict:
        """创建反思日志"""
        # Analyze reflection depth
        from core.agency_engine import AgencyEngine
        engine = AgencyEngine(self.db)
        depth = engine._compute_s4_from_text(content)
        depth_level = self._depth_to_level(depth)

        # Get current agency mode
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        agency_mode = journey.agency_mode if journey else "passive"

        entry = ReflectionJournal(
            user_id=user_id,
            title=title,
            content=content,
            journal_type=journal_type,
            reflection_depth=depth,
            depth_level=depth_level,
            agency_mode_at_time=agency_mode,
            tags=tags or [],
            prompt_used=prompt_used,
        )
        self.db.add(entry)
        self.db.flush()

        return {
            "id": entry.id,
            "user_id": user_id,
            "title": title,
            "journal_type": journal_type,
            "reflection_depth": round(depth, 3),
            "depth_level": depth_level,
            "agency_mode": agency_mode,
            "created_at": str(entry.created_at) if entry.created_at else None,
        }

    def list_entries(
        self,
        user_id: int,
        journal_type: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """列出反思日志"""
        q = self.db.query(ReflectionJournal).filter(
            ReflectionJournal.user_id == user_id
        )
        if journal_type:
            q = q.filter(ReflectionJournal.journal_type == journal_type)

        total = q.count()
        entries = q.order_by(desc(ReflectionJournal.created_at)).offset(offset).limit(limit).all()

        return {
            "total": total,
            "entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "content_preview": (e.content[:100] + "...") if len(e.content) > 100 else e.content,
                    "journal_type": e.journal_type,
                    "reflection_depth": float(e.reflection_depth) if e.reflection_depth else 0,
                    "depth_level": e.depth_level,
                    "tags": e.tags or [],
                    "created_at": str(e.created_at) if e.created_at else None,
                }
                for e in entries
            ],
        }

    def get_entry(self, entry_id: int, user_id: int) -> dict:
        """获取单条反思日志"""
        entry = self.db.query(ReflectionJournal).filter(
            ReflectionJournal.id == entry_id,
            ReflectionJournal.user_id == user_id,
        ).first()
        if not entry:
            return {"error": "日志不存在"}
        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "title": entry.title,
            "content": entry.content,
            "journal_type": entry.journal_type,
            "reflection_depth": float(entry.reflection_depth) if entry.reflection_depth else 0,
            "depth_level": entry.depth_level,
            "agency_mode_at_time": entry.agency_mode_at_time,
            "tags": entry.tags or [],
            "prompt_used": entry.prompt_used,
            "created_at": str(entry.created_at) if entry.created_at else None,
            "updated_at": str(entry.updated_at) if entry.updated_at else None,
        }

    def get_prompts(self, user_id: int) -> dict:
        """获取基于用户agency_mode的反思提示"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        mode = journey.agency_mode if journey else "passive"
        return {
            "agency_mode": mode,
            "prompts": REFLECTION_PROMPTS.get(mode, REFLECTION_PROMPTS["passive"]),
        }

    def get_depth_stats(self, user_id: int, days: int = 30) -> dict:
        """获取反思深度统计"""
        since = datetime.utcnow() - timedelta(days=days)
        entries = self.db.query(ReflectionJournal).filter(
            ReflectionJournal.user_id == user_id,
            ReflectionJournal.created_at >= since,
        ).all()

        if not entries:
            return {"total_entries": 0, "avg_depth": 0, "depth_distribution": {}}

        depths = [float(e.reflection_depth) for e in entries if e.reflection_depth]
        avg_depth = sum(depths) / len(depths) if depths else 0

        distribution = {}
        for e in entries:
            level = e.depth_level or "surface"
            distribution[level] = distribution.get(level, 0) + 1

        return {
            "total_entries": len(entries),
            "avg_depth": round(avg_depth, 3),
            "depth_distribution": distribution,
            "days": days,
        }

    def _depth_to_level(self, depth: float) -> str:
        if depth >= 0.8:
            return "identity"
        elif depth >= 0.5:
            return "insight"
        elif depth >= 0.2:
            return "pattern"
        return "surface"
