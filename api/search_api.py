# -*- coding: utf-8 -*-
"""
P6A 全平台搜索 API — GET /api/v1/search
三端权限隔离: admin(全量) / coach(绑定学员) / client(仅自己)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.models import User, ROLE_LEVEL
from api.dependencies import get_current_user
from api.search_service import MODULE_SEARCH_FN

router = APIRouter(tags=["search"])

_VALID_MODULES = set(MODULE_SEARCH_FN.keys())


def _resolve_role(user: User) -> str:
    level = ROLE_LEVEL.get(user.role, 1)
    if level >= 99:
        return "admin"
    if level >= 4:
        return "coach"
    return "client"


@router.get("/api/v1/users/search")
async def users_search(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """用户搜索 — 前端别名，转发到统一搜索的 users 模块"""
    role = _resolve_role(current_user)
    try:
        items = await MODULE_SEARCH_FN["users"](db, q, role, current_user.id, limit)
    except Exception:
        items = []
    return {"query": q, "items": items, "total": len(items)}


@router.get("/api/v1/search")
async def unified_search(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    modules: str = Query(
        "users,prescriptions,tasks,checkins,content",
        description="逗号分隔模块名",
    ),
    limit: int = Query(5, ge=1, le=20, description="每模块最大返回条数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """全平台搜索 — 支持 users/prescriptions/tasks/checkins/content 五模块"""
    role = _resolve_role(current_user)
    requested = [m.strip() for m in modules.split(",") if m.strip() in _VALID_MODULES]
    if not requested:
        return {"query": q, "role": role, "results": {}, "total": 0}

    # 顺序搜索 (AsyncSession 不支持并发操作)
    results = {}
    total = 0
    for mod in requested:
        try:
            items = await MODULE_SEARCH_FN[mod](db, q, role, current_user.id, limit)
            results[mod] = items
            total += len(items)
        except Exception as exc:
            results[mod] = {"error": str(exc), "items": []}

    return {"query": q, "role": role, "results": results, "total": total}


@router.get("/api/v1/leaderboard/credits")
async def credits_leaderboard(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """学分排行榜 — 按 total_points 降序"""
    rows = (await db.execute(sa_text("""
        SELECT uls.user_id, uls.total_points,
               u.full_name, u.username, u.avatar_url
        FROM user_learning_stats uls
        JOIN users u ON u.id = uls.user_id
        ORDER BY uls.total_points DESC
        LIMIT :lim
    """), {"lim": limit})).mappings().all()

    items = []
    my_rank = None
    my_points = 0
    for i, r in enumerate(rows, 1):
        pts = r["total_points"] or 0
        if r["user_id"] == current_user.id:
            my_rank = i
            my_points = pts
        items.append({
            "rank": i,
            "user_id": r["user_id"],
            "name": r["full_name"] or r["username"],
            "avatar_url": r["avatar_url"] or "",
            "points": pts,
        })

    # 当前用户不在榜单前 N 名时，单独查询积分
    if my_rank is None:
        row = (await db.execute(sa_text(
            "SELECT total_points FROM user_learning_stats WHERE user_id = :uid"
        ), {"uid": current_user.id})).mappings().first()
        if row:
            my_points = row["total_points"] or 0

    return {"items": items, "my_rank": my_rank, "my_points": my_points, "total": len(items)}
