"""
P6A 全平台搜索服务 — 5个模块 × 3端权限隔离
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Coach 权限子查询: 仅返回绑定学员
_COACH_STUDENT_FILTER = """
    AND t.user_id IN (
        SELECT student_id FROM coach_schema.coach_student_bindings
        WHERE coach_id = :me AND is_active = true
    )
"""


async def search_users(
    db: AsyncSession, q: str, role: str, user_id: int, limit: int = 5
) -> list[dict]:
    """搜索用户 — admin全量, coach仅绑定学员, client仅自己"""
    base = """
        SELECT id, username, full_name, nickname, role::text AS role,
               is_active, created_at
        FROM users
        WHERE (username ILIKE :q OR full_name ILIKE :q OR nickname ILIKE :q)
    """
    if role == "admin":
        sql = base + " ORDER BY created_at DESC LIMIT :lim"
    elif role == "coach":
        sql = (
            base
            + " AND id IN ("
            "  SELECT student_id FROM coach_schema.coach_student_bindings"
            "  WHERE coach_id = :me AND is_active = true"
            ") ORDER BY created_at DESC LIMIT :lim"
        )
    else:
        sql = base + " AND id = :me ORDER BY created_at DESC LIMIT :lim"

    rows = (await db.execute(text(sql), {"q": f"%{q}%", "me": user_id, "lim": limit})).mappings().all()
    return [dict(r) for r in rows]


async def search_prescriptions(
    db: AsyncSession, q: str, role: str, user_id: int, limit: int = 5
) -> list[dict]:
    """搜索行为处方 — admin全量, coach仅绑定学员, client仅自己"""
    base = """
        SELECT t.id, t.user_id, t.target_behavior, t.domain,
               t.status, t.created_at
        FROM behavior_prescriptions t
        WHERE (t.target_behavior ILIKE :q OR t.domain ILIKE :q)
    """
    if role == "admin":
        sql = base + " ORDER BY t.created_at DESC LIMIT :lim"
    elif role == "coach":
        sql = base + _COACH_STUDENT_FILTER + " ORDER BY t.created_at DESC LIMIT :lim"
    else:
        sql = base + " AND t.user_id = :me ORDER BY t.created_at DESC LIMIT :lim"

    rows = (await db.execute(text(sql), {"q": f"%{q}%", "me": user_id, "lim": limit})).mappings().all()
    return [dict(r) for r in rows]


async def search_tasks(
    db: AsyncSession, q: str, role: str, user_id: int, limit: int = 5
) -> list[dict]:
    """搜索每日任务 — admin全量, coach仅绑定学员, client仅自己"""
    base = """
        SELECT t.id, t.user_id, t.title, t.tag, t.task_date,
               t.done, t.source, t.created_at
        FROM daily_tasks t
        WHERE (t.title ILIKE :q OR t.tag ILIKE :q)
    """
    if role == "admin":
        sql = base + " ORDER BY t.created_at DESC LIMIT :lim"
    elif role == "coach":
        sql = base + _COACH_STUDENT_FILTER + " ORDER BY t.created_at DESC LIMIT :lim"
    else:
        sql = base + " AND t.user_id = :me ORDER BY t.created_at DESC LIMIT :lim"

    rows = (await db.execute(text(sql), {"q": f"%{q}%", "me": user_id, "lim": limit})).mappings().all()
    return [dict(r) for r in rows]


async def search_checkins(
    db: AsyncSession, q: str, role: str, user_id: int, limit: int = 5
) -> list[dict]:
    """搜索签到记录 — admin全量, coach仅绑定学员, client仅自己"""
    base = """
        SELECT tc.id, tc.user_id, tc.note, tc.points_earned, tc.checked_at,
               dt.title AS task_title
        FROM task_checkins tc
        JOIN daily_tasks dt ON dt.id = tc.task_id
        WHERE (tc.note ILIKE :q OR dt.title ILIKE :q)
    """
    if role == "admin":
        sql = base + " ORDER BY tc.checked_at DESC LIMIT :lim"
    elif role == "coach":
        sql = (
            base
            + " AND tc.user_id IN ("
            "  SELECT student_id FROM coach_schema.coach_student_bindings"
            "  WHERE coach_id = :me AND is_active = true"
            ") ORDER BY tc.checked_at DESC LIMIT :lim"
        )
    else:
        sql = base + " AND tc.user_id = :me ORDER BY tc.checked_at DESC LIMIT :lim"

    rows = (await db.execute(text(sql), {"q": f"%{q}%", "me": user_id, "lim": limit})).mappings().all()
    return [dict(r) for r in rows]


async def search_content(
    db: AsyncSession, q: str, role: str, user_id: int, limit: int = 5
) -> list[dict]:
    """搜索学习内容 — 三端同权限, 仅搜已发布内容"""
    sql = """
        SELECT id, title, content_type, domain, level,
               view_count, created_at
        FROM content_items
        WHERE status = 'published'
          AND (title ILIKE :q OR domain ILIKE :q)
        ORDER BY view_count DESC, created_at DESC
        LIMIT :lim
    """
    rows = (await db.execute(text(sql), {"q": f"%{q}%", "lim": limit})).mappings().all()
    return [dict(r) for r in rows]


# 模块名 → 搜索函数映射
MODULE_SEARCH_FN = {
    "users": search_users,
    "prescriptions": search_prescriptions,
    "tasks": search_tasks,
    "checkins": search_checkins,
    "content": search_content,
}
