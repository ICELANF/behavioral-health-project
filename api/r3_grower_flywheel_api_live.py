"""
R3 (最终版): Grower 飞轮 API — 真实DB + 个性化庆祝

已合并 PATCH-4: 打卡反馈从 random.choice → 个性化引擎

部署: 替换 api/grower_flywheel_api.py
"""

import random
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["grower-flywheel"])


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════

class TodayAction(BaseModel):
    id: str
    order: int
    title: str
    tag: str
    tag_color: str
    time_hint: str
    input_mode: Optional[str] = None
    quick_label: str = "打卡"
    done: bool = False
    done_time: Optional[str] = None
    source: str = "rx"
    agent_id: Optional[str] = None


class TodayTasksResponse(BaseModel):
    date: str
    tasks: list[TodayAction]
    done_count: int
    total_count: int
    completion_pct: int
    streak_days: int


class CheckinRequest(BaseModel):
    note: Optional[str] = None
    photo_url: Optional[str] = None
    value: Optional[float] = None
    voice_url: Optional[str] = None


class CheckinResponse(BaseModel):
    success: bool
    task_id: str
    done_time: str
    streak_days: int
    message: str
    emoji: str
    points_earned: int = 0
    badge_unlocked: Optional[str] = None


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    today_completed: bool
    last_checkin_date: Optional[str] = None


class CoachTipResponse(BaseModel):
    tip: str
    tip_type: str
    agent_id: str


class WeekDay(BaseModel):
    label: str
    date: str
    status: str


class WeeklySummaryResponse(BaseModel):
    days: list[WeekDay]
    week_completion_pct: int
    best_day: Optional[str] = None


# ═══════════════════════════════════════════════════
# GET /daily-tasks/today — 真实DB
# ═══════════════════════════════════════════════════

@router.get("/daily-tasks/today", response_model=TodayTasksResponse)
async def get_today_tasks(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日行动列表 — 从 daily_tasks 表读取, 无数据时实时生成"""
    today = date.today()
    user_id = current_user.id

    stmt = text("""
        SELECT id, order_num, title, tag, tag_color, time_hint,
               input_mode, quick_label, source, agent_id, done, done_time
        FROM daily_tasks WHERE user_id = :uid AND task_date = :today
        ORDER BY order_num
    """)
    result = await db.execute(stmt, {"uid": user_id, "today": today})
    rows = result.mappings().all()

    if not rows:
        try:
            from api.r2_scheduler_agent import generate_daily_tasks_for_user
            await generate_daily_tasks_for_user(db, user_id, today)
            result = await db.execute(stmt, {"uid": user_id, "today": today})
            rows = result.mappings().all()
        except Exception:
            await db.rollback()

    streak_days = await _get_streak_days(db, user_id)

    tasks = [
        TodayAction(
            id=r["id"], order=r["order_num"], title=r["title"],
            tag=r["tag"], tag_color=r["tag_color"],
            time_hint=r["time_hint"] or "",
            input_mode=r["input_mode"],
            quick_label=r["quick_label"] or "打卡",
            done=bool(r["done"]),
            done_time=r["done_time"].strftime("%H:%M") if r["done_time"] else None,
            source=r["source"] or "rx", agent_id=r["agent_id"],
        )
        for r in rows
    ]

    done_count = sum(1 for t in tasks if t.done)
    total_count = len(tasks)

    return TodayTasksResponse(
        date=today.isoformat(), tasks=tasks,
        done_count=done_count, total_count=total_count,
        completion_pct=int(done_count / total_count * 100) if total_count > 0 else 0,
        streak_days=streak_days,
    )


# ═══════════════════════════════════════════════════
# POST /daily-tasks/:id/checkin — 真实DB + 个性化反馈
# ═══════════════════════════════════════════════════

@router.post("/daily-tasks/{task_id}/checkin", response_model=CheckinResponse)
async def checkin_task(
    task_id: str = Path(...),
    body: CheckinRequest = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """任务打卡 — 写DB + 更新streak + 个性化反馈 + 里程碑检查"""
    if body is None:
        body = CheckinRequest()

    user_id = current_user.id
    now = datetime.now()

    # 验证任务归属
    task_result = await db.execute(text("""
        SELECT id, user_id, done, title, tag FROM daily_tasks WHERE id = :tid AND user_id = :uid
    """), {"tid": task_id, "uid": user_id})
    task = task_result.mappings().first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或不属于当前用户")
    if task["done"]:
        raise HTTPException(status_code=409, detail="任务已完成，不可重复打卡")

    # 写入打卡记录
    await db.execute(text("""
        INSERT INTO task_checkins (task_id, user_id, note, photo_url, value, voice_url, points_earned, checked_at)
        VALUES (:tid, :uid, :note, :photo, :val, :voice, 10, :now)
    """), {"tid": task_id, "uid": user_id, "note": body.note, "photo": body.photo_url,
           "val": body.value, "voice": body.voice_url, "now": now})

    # 更新任务状态
    await db.execute(text("UPDATE daily_tasks SET done = true, done_time = :now WHERE id = :tid"),
                     {"tid": task_id, "now": now})

    # 更新streak
    streak_days = await _update_streak(db, user_id, now.date())

    # 累加积分
    await db.execute(text("UPDATE users SET growth_points = COALESCE(growth_points, 0) + 10 WHERE id = :uid"),
                     {"uid": user_id})

    await db.commit()

    # ── 信任分更新 (异步桥接同步服务) ──
    try:
        import asyncio
        from core.trust_score_service import extract_trust_signals_from_checkins, TrustScoreService
        from core.database import get_db_session

        def _update_trust():
            with get_db_session() as sync_db:
                signals = extract_trust_signals_from_checkins(sync_db, user_id, days=7)
                svc = TrustScoreService(sync_db)
                svc.update_user_trust(user_id, signals, source="task_checkin")
                sync_db.commit()

        await asyncio.to_thread(_update_trust)
    except Exception:
        pass  # 信任分更新失败不影响打卡主流程

    # 检查全部完成
    counts = (await db.execute(text("""
        SELECT COUNT(*) as total, SUM(CASE WHEN done THEN 1 ELSE 0 END) as done_count
        FROM daily_tasks WHERE user_id = :uid AND task_date = :today
    """), {"uid": user_id, "today": now.date()})).mappings().first()
    all_done = counts["total"] > 0 and counts["done_count"] == counts["total"]

    # ── 个性化反馈 (PATCH-4 合并) ──
    fb = await _build_personalized_feedback(db, user_id, streak_days, task["tag"] or "", all_done)
    badge = "daily_complete" if all_done and streak_days >= 7 else None

    # ── 里程碑检查 (R7 合并) ──
    try:
        from api.r7_notification_agent import check_and_send_milestone
        await check_and_send_milestone(db, user_id, streak_days)
    except Exception:
        pass

    return CheckinResponse(
        success=True, task_id=task_id, done_time=now.strftime("%H:%M"),
        streak_days=streak_days, message=fb["message"], emoji=fb["emoji"],
        points_earned=10, badge_unlocked=badge,
    )


# ═══════════════════════════════════════════════════
# GET /user/streak — 真实DB
# ═══════════════════════════════════════════════════

@router.get("/user/streak", response_model=StreakResponse)
async def get_user_streak(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id
    stmt = text("SELECT current_streak, longest_streak, last_checkin_date FROM user_streaks WHERE user_id = :uid")
    row = (await db.execute(stmt, {"uid": user_id})).mappings().first()

    if not row:
        return StreakResponse(current_streak=0, longest_streak=0, today_completed=False)

    today = date.today()
    current = row["current_streak"] or 0
    if row["last_checkin_date"] and row["last_checkin_date"] < today - timedelta(days=1):
        current = 0

    return StreakResponse(
        current_streak=current, longest_streak=row["longest_streak"] or 0,
        today_completed=(row["last_checkin_date"] == today) if row["last_checkin_date"] else False,
        last_checkin_date=row["last_checkin_date"].isoformat() if row["last_checkin_date"] else None,
    )


# ═══════════════════════════════════════════════════
# GET /coach-tip/today — 基于状态的规则引擎
# ═══════════════════════════════════════════════════

@router.get("/coach-tip/today", response_model=CoachTipResponse)
async def get_coach_tip_today(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id
    today = date.today()

    result = (await db.execute(text("""
        SELECT COUNT(*) as total, SUM(CASE WHEN done THEN 1 ELSE 0 END) as done_count
        FROM daily_tasks WHERE user_id = :uid AND task_date = :today
    """), {"uid": user_id, "today": today})).mappings().first()
    total, done = result["total"] or 0, result["done_count"] or 0
    streak = await _get_streak_days(db, user_id)

    if total == 0:
        tip, tip_type = "今天还没有任务安排，要不要和我聊聊您的健康目标？", "suggestion"
    elif done == total:
        tip, tip_type = f"太棒了！今天的任务全部完成，已经连续坚持{streak}天了！", "celebration"
    elif done > 0:
        tip, tip_type = f"已经完成{done}/{total}个任务了，离今天的目标更近了一步！", "encouragement"
    elif streak >= 3:
        tip, tip_type = f"您已经连续{streak}天照顾自己了，今天继续保持这份好状态！", "encouragement"
    else:
        tip, tip_type = "新的一天开始了，从第一个小任务开始吧，一步一步来。", "suggestion"

    return CoachTipResponse(tip=tip, tip_type=tip_type, agent_id="behavior_coach")


# ═══════════════════════════════════════════════════
# GET /weekly-summary — 真实DB聚合
# ═══════════════════════════════════════════════════

@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    labels = ["一", "二", "三", "四", "五", "六", "日"]
    days, total_tasks, total_done, best_pct, best_day = [], 0, 0, -1, None

    for i in range(7):
        d = monday + timedelta(days=i)
        if d > today:
            days.append(WeekDay(label=labels[i], date=d.isoformat(), status="future"))
            continue

        r = (await db.execute(text("""
            SELECT COUNT(*) as total, SUM(CASE WHEN done THEN 1 ELSE 0 END) as done_count
            FROM daily_tasks WHERE user_id = :uid AND task_date = :d
        """), {"uid": user_id, "d": d})).mappings().first()
        t, dc = r["total"] or 0, r["done_count"] or 0
        total_tasks += t
        total_done += dc

        if d == today:
            status = "today"
        elif t == 0:
            status = "missed"
        elif dc >= t:
            status = "full"
        elif dc > 0:
            status = "partial"
        else:
            status = "missed"

        if t > 0 and dc / t * 100 > best_pct:
            best_pct = dc / t * 100
            best_day = labels[i]

        days.append(WeekDay(label=labels[i], date=d.isoformat(), status=status))

    return WeeklySummaryResponse(
        days=days,
        week_completion_pct=int(total_done / total_tasks * 100) if total_tasks > 0 else 0,
        best_day=best_day,
    )


# ═══════════════════════════════════════════════════
# 个性化反馈引擎 (PATCH-4 合并)
# ═══════════════════════════════════════════════════

MILESTONE_FEEDBACK = {
    7: "🔥", 14: "⭐", 21: "💪", 30: "🏆", 60: "🎉", 90: "👑",
}

TAG_FEEDBACK = {
    "营养": {"emoji": "🥗", "message": "记录饮食是改变的第一步！"},
    "运动": {"emoji": "🏃", "message": "动起来了！身体会感谢您的。"},
    "监测": {"emoji": "📊", "message": "数据记录好了，心里有数！"},
    "睡眠": {"emoji": "😴", "message": "关注睡眠，身体会慢慢好起来。"},
    "情绪": {"emoji": "💚", "message": "关注自己的感受，这很重要。"},
}

GENERIC_FEEDBACK = [
    {"emoji": "🎉", "message": "太棒了！"},
    {"emoji": "💪", "message": "做到了！"},
    {"emoji": "✨", "message": "继续保持！"},
    {"emoji": "🔥", "message": "又进一步！"},
    {"emoji": "👏", "message": "好样的！"},
    {"emoji": "⭐", "message": "坚持就是胜利！"},
]


async def _build_personalized_feedback(
    db: AsyncSession, user_id: int,
    streak_days: int, task_tag: str, all_done: bool
) -> dict:
    """
    个性化打卡反馈 — 替代原 random.choice
    优先级: 里程碑 > 全部完成 > 用户上下文 > 标签匹配 > 通用
    """
    # 1. 里程碑
    if streak_days in MILESTONE_FEEDBACK:
        return {"emoji": MILESTONE_FEEDBACK[streak_days],
                "message": f"连续{streak_days}天！您的坚持正在改变生活。"}

    # 2. 全部完成
    if all_done:
        return {"emoji": "🏆", "message": "今天全部完成！太厉害了！"}

    # 3. 用户上下文个性化
    try:
        from api.r8_user_context import load_user_context
        ctx = await load_user_context(db, user_id, categories=["preference", "social"])
        if ctx.get("social", {}).get("has_grandchildren"):
            return {"emoji": "✨", "message": "做到了！给孙子做个好榜样！"}
        if ctx.get("preference", {}).get("motivation"):
            return {"emoji": "✨", "message": f"做到了！{ctx['preference']['motivation']}"}
    except Exception:
        pass

    # 4. 标签匹配
    if task_tag in TAG_FEEDBACK:
        return TAG_FEEDBACK[task_tag]

    # 5. 通用
    return random.choice(GENERIC_FEEDBACK)


# ═══════════════════════════════════════════════════
# 内部辅助
# ═══════════════════════════════════════════════════

async def _get_streak_days(db: AsyncSession, user_id: int) -> int:
    row = (await db.execute(
        text("SELECT current_streak, last_checkin_date FROM user_streaks WHERE user_id = :uid"),
        {"uid": user_id}
    )).mappings().first()
    if not row:
        return 0
    if row["last_checkin_date"] and row["last_checkin_date"] < date.today() - timedelta(days=1):
        return 0
    return row["current_streak"] or 0


async def _update_streak(db: AsyncSession, user_id: int, today: date) -> int:
    row = (await db.execute(
        text("SELECT current_streak, longest_streak, last_checkin_date FROM user_streaks WHERE user_id = :uid"),
        {"uid": user_id}
    )).mappings().first()

    if not row:
        await db.execute(text("""
            INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_checkin_date, updated_at)
            VALUES (:uid, 1, 1, :today, NOW())
        """), {"uid": user_id, "today": today})
        return 1

    last_date = row["last_checkin_date"]
    current = row["current_streak"] or 0
    longest = row["longest_streak"] or 0

    if last_date == today:
        return current
    new_streak = current + 1 if last_date == today - timedelta(days=1) else 1
    new_longest = max(longest, new_streak)

    await db.execute(text("""
        UPDATE user_streaks
        SET current_streak = :streak, longest_streak = :longest,
            last_checkin_date = :today, updated_at = NOW()
        WHERE user_id = :uid
    """), {"streak": new_streak, "longest": new_longest, "today": today, "uid": user_id})
    return new_streak
