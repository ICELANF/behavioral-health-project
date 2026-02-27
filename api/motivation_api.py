"""
首页激励统计 API
Motivation Stats API for Home Page

端点:
- GET /api/v1/home/motivation-stats: 获取激励统计数据
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.database import get_db
from api.dependencies import get_current_user
from core.models import User
from loguru import logger

router = APIRouter(prefix="/api/v1/home", tags=["首页激励"])


@router.get("/motivation-stats")
async def get_motivation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    首页激励统计 — 聚合多张表数据

    返回: today_points, week_points, total_points, tasks_completed_total,
          current_streak, longest_streak, week_trend[], recent_badge
    """
    uid = current_user.id
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    # ── 今日积分 ──
    today_points = 0
    try:
        row = db.execute(text(
            "SELECT COALESCE(SUM(points_earned), 0) "
            "FROM task_checkins WHERE user_id = :uid "
            "AND CAST(checked_at AS date) = CURRENT_DATE"
        ), {"uid": uid}).fetchone()
        if row:
            today_points = int(row[0])
    except Exception as e:
        logger.debug(f"motivation today_points: {e}")

    # ── 本周积分 ──
    week_points = 0
    try:
        row = db.execute(text(
            "SELECT COALESCE(SUM(points_earned), 0) "
            "FROM task_checkins WHERE user_id = :uid "
            "AND checked_at >= CAST(:monday AS timestamp)"
        ), {"uid": uid, "monday": str(monday)}).fetchone()
        if row:
            week_points = int(row[0])
    except Exception as e:
        logger.debug(f"motivation week_points: {e}")

    # ── 累计积分 ──
    total_points = getattr(current_user, 'growth_points', None) or 0

    # ── 累计完成任务数 ──
    tasks_completed_total = 0
    try:
        row = db.execute(text(
            "SELECT COUNT(*) FROM task_checkins WHERE user_id = :uid"
        ), {"uid": uid}).fetchone()
        if row:
            tasks_completed_total = int(row[0])
    except Exception as e:
        logger.debug(f"motivation tasks_total: {e}")

    # ── 连续天数 ──
    current_streak = 0
    longest_streak = 0
    try:
        row = db.execute(text(
            "SELECT current_streak, longest_streak "
            "FROM user_streaks WHERE user_id = :uid"
        ), {"uid": uid}).fetchone()
        if row:
            current_streak = int(row[0] or 0)
            longest_streak = int(row[1] or 0)
    except Exception as e:
        logger.debug(f"motivation streaks: {e}")

    # ── 7日完成率趋势 ──
    week_trend = []
    try:
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            row = db.execute(text(
                "SELECT COUNT(*), COALESCE(SUM(CASE WHEN done THEN 1 ELSE 0 END), 0) "
                "FROM daily_tasks WHERE user_id = :uid AND task_date = CAST(:d AS date)"
            ), {"uid": uid, "d": str(d)}).fetchone()
            total = int(row[0]) if row else 0
            done = int(row[1]) if row else 0
            pct = round(done * 100 / total) if total > 0 else 0
            week_trend.append({"date": str(d), "pct": pct})
    except Exception as e:
        logger.debug(f"motivation week_trend: {e}")
        # fallback: 7 days of 0
        if not week_trend:
            week_trend = [{"date": str(today - timedelta(days=i)), "pct": 0} for i in range(6, -1, -1)]

    # ── 最近徽章 ──
    recent_badge = None
    try:
        row = db.execute(text(
            "SELECT b.name, b.visual_json "
            "FROM user_badges ub JOIN badges b ON ub.badge_id = b.id "
            "WHERE ub.user_id = :uid ORDER BY ub.earned_at DESC LIMIT 1"
        ), {"uid": uid}).fetchone()
        if row:
            import json
            visual = {}
            if row[1]:
                try:
                    visual = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                except Exception:
                    pass
            recent_badge = {
                "name": row[0],
                "icon": visual.get("icon", ""),
            }
    except Exception as e:
        logger.debug(f"motivation recent_badge: {e}")

    return {
        "today_points": today_points,
        "week_points": week_points,
        "total_points": total_points,
        "tasks_completed_total": tasks_completed_total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "week_trend": week_trend,
        "recent_badge": recent_badge,
    }
