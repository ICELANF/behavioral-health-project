# -*- coding: utf-8 -*-
"""
用户行为分析周报 API
GET  /api/v1/weekly-reports          — 当前用户的周报列表
GET  /api/v1/weekly-reports/latest   — 最新一期周报
GET  /api/v1/weekly-reports/{week_start} — 指定周的周报
POST /api/v1/admin/weekly-reports/generate — 手动触发生成 (admin)
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.models import User
from api.dependencies import get_current_user, require_admin

router = APIRouter(tags=["weekly-reports"])


@router.get("/api/v1/weekly-reports")
async def list_weekly_reports(
    limit: int = Query(10, ge=1, le=52),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """当前用户的周报列表 (最近N周)"""
    rows = (await db.execute(text("""
        SELECT id, week_start::text, week_end::text, tasks_total, tasks_completed,
               completion_pct, checkin_count, learning_minutes, points_earned,
               activity_count, streak_days, highlights, suggestions, created_at
        FROM user_weekly_reports
        WHERE user_id = :uid
        ORDER BY week_start DESC
        LIMIT :lim
    """), {"uid": current_user.id, "lim": limit})).mappings().all()
    return {"reports": [dict(r) for r in rows], "total": len(rows)}


@router.get("/api/v1/weekly-reports/latest")
async def latest_weekly_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """最新一期周报"""
    row = (await db.execute(text("""
        SELECT id, week_start::text, week_end::text, tasks_total, tasks_completed,
               completion_pct, checkin_count, learning_minutes, points_earned,
               activity_count, streak_days, highlights, suggestions, created_at
        FROM user_weekly_reports
        WHERE user_id = :uid
        ORDER BY week_start DESC
        LIMIT 1
    """), {"uid": current_user.id})).mappings().first()
    if not row:
        raise HTTPException(404, "暂无周报数据")
    result = dict(row)
    result["review_status"] = "auto"
    return result


@router.get("/api/v1/weekly-reports/{week_start}")
async def get_weekly_report(
    week_start: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """指定周的周报"""
    try:
        ws = date.fromisoformat(week_start)
    except ValueError:
        raise HTTPException(400, "日期格式错误，请使用 YYYY-MM-DD")
    row = (await db.execute(text("""
        SELECT id, week_start::text, week_end::text, tasks_total, tasks_completed,
               completion_pct, checkin_count, learning_minutes, points_earned,
               activity_count, streak_days, highlights, suggestions, created_at
        FROM user_weekly_reports
        WHERE user_id = :uid AND week_start = :ws
    """), {"uid": current_user.id, "ws": ws})).mappings().first()
    if not row:
        raise HTTPException(404, "该周暂无周报")
    return dict(row)


@router.post("/api/v1/admin/weekly-reports/generate")
async def admin_generate_reports(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """手动触发周报生成 (admin only)"""
    from api.weekly_report_service import generate_all_reports
    today = date.today()
    week_start = today - timedelta(days=today.weekday() + 7)  # 上周一
    week_end = week_start + timedelta(days=6)                  # 上周日
    count = await generate_all_reports(db, week_start, week_end)
    return {
        "generated": count,
        "week_start": str(week_start),
        "week_end": str(week_end),
    }
