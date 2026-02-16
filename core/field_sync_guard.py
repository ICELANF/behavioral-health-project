"""
C4 修复: 模型字段冗余治理
冲突: current_stage(×2), agency_mode(×3), agency_score(×3), trust_score(×3)
策略: JourneyStageV4 为权威源, User 同名字段为缓存快照
方案: 字段注释 + 同步守卫 + 一致性检查

文件: core/models.py (补丁) + core/field_sync_guard.py (新建)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import event, select, func
from sqlalchemy.orm import Session


# ═══════════════════════════════════════════════════════
# PATCH 1: core/models.py — 字段权威源标注
# ═══════════════════════════════════════════════════════

MODELS_ANNOTATION_PATCH = '''
# ── C4 权威源声明 ────────────────────────────────────────
# 以下字段存在冗余, 权威源与缓存关系如下:
#
# | 字段            | 权威源 (SOURCE OF TRUTH)  | 缓存 (SNAPSHOT)     |
# |----------------|--------------------------|---------------------|
# | current_stage  | JourneyStageV4           | User.current_stage  |
# | agency_mode    | JourneyStageV4           | User.agency_mode    |
# | agency_score   | JourneyStageV4           | User.agency_score   |
# | trust_score    | JourneyStageV4           | User.trust_score    |
#
# 规则:
# 1. 写入必须先写权威源, 再由 FieldSyncGuard 同步缓存
# 2. 读取: 热路径读 User(缓存), 精确查询读 JourneyStageV4(权威源)
# 3. 不一致时以 JourneyStageV4 为准
# ────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    # ... 现有字段 ...

    # C4-CACHE: 以下字段为 JourneyStageV4 的快照缓存
    # ⚠️ 不要直接写入, 使用 FieldSyncGuard.sync_user_cache()
    current_stage = Column(String(10), nullable=True,
                           comment="C4-CACHE: 权威源=JourneyStageV4.current_stage")
    agency_mode = Column(String(20), nullable=True,
                         comment="C4-CACHE: 权威源=JourneyStageV4.agency_mode")
    agency_score = Column(Float, nullable=True,
                          comment="C4-CACHE: 权威源=JourneyStageV4.agency_score")
    trust_score = Column(Float, nullable=True,
                         comment="C4-CACHE: 权威源=JourneyStageV4.trust_score")


class JourneyStageV4(Base):
    __tablename__ = "journey_stages_v4"
    # ... 现有字段 ...

    # C4-SOURCE: 以下字段为权威源
    current_stage = Column(String(10), nullable=False,
                           comment="C4-SOURCE: 阶段权威值")
    agency_mode = Column(String(20), nullable=True,
                         comment="C4-SOURCE: 自主模式权威值")
    agency_score = Column(Float, nullable=True,
                          comment="C4-SOURCE: 自主分数权威值")
    trust_score = Column(Float, nullable=True,
                         comment="C4-SOURCE: 信任分数权威值")
'''


# ═══════════════════════════════════════════════════════
# 新建: core/field_sync_guard.py — 同步守卫
# ═══════════════════════════════════════════════════════

class FieldSyncGuard:
    """
    C4 字段同步守卫

    职责:
    1. JourneyStageV4 更新后自动同步 User 缓存字段
    2. 定期一致性校验(发现不一致则修复并记录)
    3. 提供安全的写入接口(禁止直接写 User 缓存字段)
    """

    # 需要同步的字段映射: JourneyStageV4.field → User.field
    SYNC_FIELDS = [
        "current_stage",
        "agency_mode",
        "agency_score",
        "trust_score",
    ]

    def __init__(self, db: Session):
        self.db = db

    def sync_user_cache(self, user_id: int) -> dict:
        """
        从权威源(JourneyStageV4)同步到缓存(User)

        返回: {"synced": [...], "unchanged": [...]}
        """
        from core.models import User, JourneyStageV4

        # 获取权威源最新值
        stage = self.db.execute(
            select(JourneyStageV4).where(
                JourneyStageV4.user_id == user_id
            ).order_by(JourneyStageV4.updated_at.desc()).limit(1)
        )
        source = stage.scalar_one_or_none()
        if not source:
            return {"synced": [], "unchanged": self.SYNC_FIELDS,
                    "reason": "no_journey_stage"}

        user = self.db.get(User, user_id)
        if not user:
            return {"synced": [], "unchanged": self.SYNC_FIELDS,
                    "reason": "user_not_found"}

        synced = []
        unchanged = []
        for field in self.SYNC_FIELDS:
            source_val = getattr(source, field, None)
            cache_val = getattr(user, field, None)
            if source_val != cache_val:
                setattr(user, field, source_val)
                synced.append(field)
            else:
                unchanged.append(field)

        if synced:
            self.db.commit()

        return {"synced": synced, "unchanged": unchanged}

    def batch_consistency_check(self, limit: int = 500) -> dict:
        """
        批量一致性校验 — 用于定时任务

        返回: {"total_checked": N, "inconsistent": N, "fixed": N, "details": [...]}
        """
        from core.models import User, JourneyStageV4

        result = self.db.execute(
            select(User.id).where(User.is_active == True).limit(limit)
        )
        user_ids = [r[0] for r in result.all()]

        stats = {"total_checked": len(user_ids), "inconsistent": 0,
                 "fixed": 0, "details": []}

        for uid in user_ids:
            sync_result = self.sync_user_cache(uid)
            if sync_result["synced"]:
                stats["inconsistent"] += 1
                stats["fixed"] += 1
                stats["details"].append({
                    "user_id": uid,
                    "fixed_fields": sync_result["synced"],
                })

        return stats


# ═══════════════════════════════════════════════════════
# SQLAlchemy Event Hook: 自动同步
# ═══════════════════════════════════════════════════════

SQLALCHEMY_EVENT_PATCH = '''
# 添加到 core/models.py 底部或 core/database.py

from sqlalchemy import event

@event.listens_for(JourneyStageV4, "after_update")
@event.listens_for(JourneyStageV4, "after_insert")
def _auto_sync_user_cache(mapper, connection, target):
    """
    C4: JourneyStageV4 变更后自动同步 User 缓存
    注意: 此为同步event, 在同一事务内执行
    """
    from sqlalchemy import update
    sync_values = {}
    for field in ["current_stage", "agency_mode", "agency_score", "trust_score"]:
        val = getattr(target, field, None)
        if val is not None:
            sync_values[field] = val
    if sync_values:
        connection.execute(
            update(User).where(User.id == target.user_id).values(**sync_values)
        )
'''


# ═══════════════════════════════════════════════════════
# Celery 定时校验任务
# ═══════════════════════════════════════════════════════

SCHEDULER_PATCH = '''
# C4: 字段一致性定时校验
"field-consistency-check": {
    "task": "tasks.field_consistency_check",
    "schedule": crontab(minute=30, hour=4),  # 每日4:30
    "options": {"queue": "maintenance"},
},
'''

TASK_PATCH = '''
@app.task(name="tasks.field_consistency_check")
def field_consistency_check_task():
    """C4: 每日字段一致性校验+自动修复"""
    import asyncio
    from core.database import get_async_session
    from core.field_sync_guard import FieldSyncGuard

    def _run():
        async with get_async_session() as db:
            guard = FieldSyncGuard(db)
            return guard.batch_consistency_check(limit=1000)

    return asyncio.get_event_loop().run_until_complete(_run())
'''
