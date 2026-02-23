# -*- coding: utf-8 -*-
"""
Sharer(L2) 飞轮 API — 分享者专属数据端点

端点:
  GET /api/v1/sharer/mentee-progress    — 同道者进度 (4槽位)
  GET /api/v1/sharer/contribution-stats  — 投稿统计
  GET /api/v1/sharer/influence-score     — 影响力积分
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

logger = logging.getLogger("sharer_flywheel")

router = APIRouter(prefix="/api/v1/sharer", tags=["sharer-flywheel"])


# ═══════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════

class MenteeSlot(BaseModel):
    user_id: int | None = None
    name: str = ""
    role: str = ""
    status: str = "empty"  # active / graduated / empty
    streak: int = 0
    today_pct: int = 0


class MenteeProgressResponse(BaseModel):
    mentees: list[MenteeSlot]
    filled: int
    total_slots: int = 4
    empty_slots: int


class ContributionStatsResponse(BaseModel):
    submitted: int = 0
    pending: int = 0
    published: int = 0
    rejected: int = 0


class InfluenceScoreResponse(BaseModel):
    total: int = 0
    likes: int = 0
    saves: int = 0
    citations: int = 0
    official_points: int = 0


# ═══════════════════════════════════════════════════
# GET /mentee-progress
# ═══════════════════════════════════════════════════

@router.get("/mentee-progress", response_model=MenteeProgressResponse)
async def get_mentee_progress(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分享者的同道者槽位进度"""
    user_id = current_user.id
    today = date.today()
    mentees: list[MenteeSlot] = []

    try:
        # 查询 companion_relations 中当前用户作为 mentor 的记录
        result = await db.execute(text("""
            SELECT cr.mentee_id, cr.status,
                   u.username, u.role,
                   COALESCE(us.current_streak, 0) AS streak,
                   (SELECT COUNT(*) FROM daily_tasks dt
                    WHERE dt.user_id = cr.mentee_id AND dt.task_date = :today) AS total_tasks,
                   (SELECT COUNT(*) FROM daily_tasks dt
                    WHERE dt.user_id = cr.mentee_id AND dt.task_date = :today AND dt.done = true) AS done_tasks
            FROM companion_relations cr
            JOIN users u ON u.id = cr.mentee_id
            LEFT JOIN user_streaks us ON us.user_id = cr.mentee_id
            WHERE cr.mentor_id = :uid
            ORDER BY cr.created_at
            LIMIT 4
        """), {"uid": user_id, "today": today})
        rows = result.mappings().all()

        for r in rows:
            total = r["total_tasks"] or 0
            done = r["done_tasks"] or 0
            pct = int(done / total * 100) if total > 0 else 0
            mentees.append(MenteeSlot(
                user_id=r["mentee_id"],
                name=r["username"] or f"用户{r['mentee_id']}",
                role=(r["role"] or "observer").lower(),
                status=r["status"] or "active",
                streak=r["streak"] or 0,
                today_pct=pct,
            ))
    except Exception as e:
        logger.warning(f"mentee-progress query failed: {e}")

    filled = len(mentees)
    empty = 4 - filled
    # 填充空位
    for _ in range(empty):
        mentees.append(MenteeSlot())

    return MenteeProgressResponse(
        mentees=mentees, filled=filled, empty_slots=empty,
    )


# ═══════════════════════════════════════════════════
# GET /contribution-stats
# ═══════════════════════════════════════════════════

@router.get("/contribution-stats", response_model=ContributionStatsResponse)
async def get_contribution_stats(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分享者的投稿统计"""
    user_id = current_user.id
    submitted = pending = published = rejected = 0

    try:
        # knowledge_documents 投稿统计
        result = await db.execute(text("""
            SELECT review_status, COUNT(*) AS cnt
            FROM knowledge_documents
            WHERE contributor_id = :uid
            GROUP BY review_status
        """), {"uid": user_id})
        for r in result.mappings().all():
            status = (r["review_status"] or "").lower()
            cnt = r["cnt"] or 0
            submitted += cnt
            if status == "pending":
                pending += cnt
            elif status in ("approved", "published"):
                published += cnt
            elif status in ("rejected",):
                rejected += cnt
    except Exception as e:
        logger.warning(f"contribution-stats query failed: {e}")

    # 补充 content_items 中 author_id 匹配的已发布内容
    try:
        result = await db.execute(text("""
            SELECT COUNT(*) AS cnt FROM content_items
            WHERE author_id = :uid AND status = 'published'
        """), {"uid": user_id})
        row = result.mappings().first()
        if row and row["cnt"]:
            published += row["cnt"]
            submitted += row["cnt"]
    except Exception:
        pass

    return ContributionStatsResponse(
        submitted=submitted, pending=pending,
        published=published, rejected=rejected,
    )


# ═══════════════════════════════════════════════════
# GET /influence-score
# ═══════════════════════════════════════════════════

@router.get("/influence-score", response_model=InfluenceScoreResponse)
async def get_influence_score(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分享者的影响力积分详情"""
    user_id = current_user.id
    likes = saves = official = 0

    # 从 content_items 聚合被赞/被藏数
    try:
        result = await db.execute(text("""
            SELECT COALESCE(SUM(like_count), 0) AS likes,
                   COALESCE(SUM(collect_count), 0) AS saves
            FROM content_items
            WHERE author_id = :uid
        """), {"uid": user_id})
        row = result.mappings().first()
        if row:
            likes = row["likes"] or 0
            saves = row["saves"] or 0
    except Exception as e:
        logger.warning(f"influence-score content query failed: {e}")

    # 从 user_learning_stats 读取官方影响力积分
    try:
        result = await db.execute(text("""
            SELECT COALESCE(influence_points, 0) AS ip
            FROM user_learning_stats
            WHERE user_id = :uid
        """), {"uid": user_id})
        row = result.mappings().first()
        if row:
            official = row["ip"] or 0
    except Exception:
        pass

    total = official + likes + saves * 2

    return InfluenceScoreResponse(
        total=total, likes=likes, saves=saves,
        citations=0, official_points=official,
    )
