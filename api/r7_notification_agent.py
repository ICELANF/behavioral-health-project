"""
R7 (最终版): notification_agent — 主动触达

已合并 PATCH-4:
  - 时间错开: 07:15/10:15/20:15 (避免与 program_push 冲突)
  - _save_notification 增加: wx_gateway 微信推送 + coach_push_queue 审批
  - 里程碑祝贺 (由 R3 打卡时调用)

部署:
  1. 复制到 api/ 目录
  2. 在 scheduler.py 注册 3 个定时任务 (见 register_notification_jobs)
  3. 在 main.py 注册 notif_router
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("notification_agent")


# ═══════════════════════════════════════════════════
# 通知模板
# ═══════════════════════════════════════════════════

MORNING_TEMPLATES = {
    "default": "早上好！今天有{count}个小任务等您完成。第一个是：{first_task}。一步一步来 🌅",
    "streak_3": "连续第{streak}天了！今天{count}个任务，从{first_task}开始吧 💪",
    "streak_7": "整整一周了！您连续7天照顾自己，这份坚持很了不起。今天继续 🔥",
    "streak_14": "两周了！{streak}天的坚持让改变真正发生。今天{count}个任务等着您 ⭐",
    "streak_30": "一个月！30天前的您不会想到今天的自己。继续！🏆",
    "streak_60": "60天，这已经不是坚持，而是您的生活方式了。为自己骄傲 🎉",
}

EVENING_TEMPLATE = "今天还有{remaining}个任务没完成。没关系，能做多少算多少，明天继续 🌙"
RECONNECT_TEMPLATE = "好久不见！昨天没看到您的打卡记录，一切都好吗？随时可以回来，我们在这里 🤗"

RECONNECT_STREAK_TEMPLATES = {
    "long":   "您之前连续{streak}天打卡，这份坚持非常了不起。昨天没看到您，一切都好吗？休息也是照顾自己的方式，我们随时等您回来 🤗",
    "medium": "连续{streak}天的记录中断了。没关系，每一天都是新的开始。今天回来试试？哪怕只做一件小事也好 💪",
    "short":  RECONNECT_TEMPLATE,  # fallback to original
}

MILESTONE_MESSAGES = {
    7: "整整一周！连续7天照顾自己，您已经迈出了最难的那一步 🔥",
    14: "两周了！这不是运气，这是您的决心在发光 ⭐",
    21: "21天，一个习惯的养成周期。您做到了！💪",
    30: "一个月！30天前的自己一定想不到今天的改变 🏆",
    60: "60天。这已经不是坚持，这是您的新生活方式 🎉",
    90: "90天！三个月的蜕变，您是自己最好的健康管理师 👑",
    180: "半年了。180天的累积，每一天都在让您离健康更近 🌟",
    365: "一整年！365天的坚持，您已经重新定义了自己的人生 🎊",
}


# ═══════════════════════════════════════════════════
# 内容构建
# ═══════════════════════════════════════════════════

def build_morning_notification(task_count: int, first_task: str, streak_days: int) -> dict:
    if streak_days >= 60:
        tpl = MORNING_TEMPLATES["streak_60"]
    elif streak_days >= 30:
        tpl = MORNING_TEMPLATES["streak_30"]
    elif streak_days >= 14:
        tpl = MORNING_TEMPLATES["streak_14"]
    elif streak_days >= 7:
        tpl = MORNING_TEMPLATES["streak_7"]
    elif streak_days >= 3:
        tpl = MORNING_TEMPLATES["streak_3"]
    else:
        tpl = MORNING_TEMPLATES["default"]

    body = tpl.format(count=task_count, first_task=first_task, streak=streak_days)
    return {"title": "今日健康行动", "body": body, "type": "morning_task"}


# ═══════════════════════════════════════════════════
# 定时任务: 早晨推送 (07:15)
# ═══════════════════════════════════════════════════

async def send_morning_notifications(db: AsyncSession):
    today = date.today()
    stmt = text("""
        SELECT DISTINCT dt.user_id,
               us.current_streak,
               (SELECT title FROM daily_tasks
                WHERE user_id = dt.user_id AND task_date = :today
                ORDER BY order_num LIMIT 1) as first_task,
               (SELECT COUNT(*) FROM daily_tasks
                WHERE user_id = dt.user_id AND task_date = :today) as task_count
        FROM daily_tasks dt
        LEFT JOIN user_streaks us ON us.user_id = dt.user_id
        WHERE dt.task_date = :today
    """)
    users = (await db.execute(stmt, {"today": today})).mappings().all()

    sent = 0
    for u in users:
        if not u["task_count"]:
            continue
        notif = build_morning_notification(
            u["task_count"], u["first_task"] or "健康行动", u["current_streak"] or 0)
        await _save_notification(db, u["user_id"], notif["title"], notif["body"], notif["type"])
        sent += 1

    await db.commit()
    logger.info(f"早晨推送完成: {sent} 条")
    return sent


# ═══════════════════════════════════════════════════
# 定时任务: 晚间提醒 (20:15)
# ═══════════════════════════════════════════════════

async def send_evening_reminders(db: AsyncSession):
    today = date.today()
    stmt = text("""
        SELECT dt.user_id, COUNT(*) FILTER (WHERE NOT dt.done) as remaining
        FROM daily_tasks dt WHERE dt.task_date = :today
        GROUP BY dt.user_id HAVING COUNT(*) FILTER (WHERE NOT dt.done) > 0
    """)
    users = (await db.execute(stmt, {"today": today})).mappings().all()

    sent = 0
    for u in users:
        body = EVENING_TEMPLATE.format(remaining=u["remaining"])
        await _save_notification(db, u["user_id"], "今日任务提醒", body, "evening_reminder")
        sent += 1

    await db.commit()
    logger.info(f"晚间提醒完成: {sent} 条")
    return sent


# ═══════════════════════════════════════════════════
# 定时任务: 断连提醒 (10:15)
# ═══════════════════════════════════════════════════

async def send_reconnect_reminders(db: AsyncSession):
    yesterday = date.today() - timedelta(days=1)
    stmt = text("""
        SELECT us.user_id, us.current_streak
        FROM user_streaks us
        WHERE us.current_streak >= 3 AND us.last_checkin_date < :yesterday
    """)
    users = (await db.execute(stmt, {"yesterday": yesterday})).mappings().all()

    sent = 0
    for u in users:
        streak = u["current_streak"] or 0
        if streak >= 14:
            body = RECONNECT_STREAK_TEMPLATES["long"].format(streak=streak)
        elif streak >= 7:
            body = RECONNECT_STREAK_TEMPLATES["medium"].format(streak=streak)
        else:
            body = RECONNECT_STREAK_TEMPLATES["short"]
        await _save_notification(db, u["user_id"], "想念您的打卡", body, "reconnect")
        sent += 1

    await db.commit()
    logger.info(f"断连提醒完成: {sent} 条")
    return sent


# ═══════════════════════════════════════════════════
# 里程碑祝贺 (由 R3 打卡调用)
# ═══════════════════════════════════════════════════

async def check_and_send_milestone(db: AsyncSession, user_id: int, streak_days: int):
    if streak_days in MILESTONE_MESSAGES:
        await _save_notification(
            db, user_id,
            f"🎉 连续打卡 {streak_days} 天！",
            MILESTONE_MESSAGES[streak_days],
            "milestone", priority="high",
        )
        logger.info(f"用户 {user_id} 达到 {streak_days} 天里程碑")


# ═══════════════════════════════════════════════════
# 通知存储 (PATCH-4: 融入 wx + coach_push)
# ═══════════════════════════════════════════════════

async def _save_notification(
    db: AsyncSession, user_id: int,
    title: str, body: str, notif_type: str, priority: str = "normal",
):
    """写入 notifications 表 + 尝试微信推送 + 重要通知走教练审批"""

    # 1. 写 notifications 表
    try:
        await db.execute(text("""
            INSERT INTO notifications (user_id, title, body, type, priority, is_read, created_at)
            VALUES (:uid, :title, :body, :type, :priority, false, NOW())
        """), {"uid": user_id, "title": title, "body": body,
               "type": notif_type, "priority": priority})
    except Exception as e:
        # 表不存在时自动建表
        logger.warning(f"通知写入失败: {e}，尝试建表")
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200), body TEXT, type VARCHAR(50),
                    priority VARCHAR(20) DEFAULT 'normal',
                    is_read BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notif_user_unread
                ON notifications(user_id, is_read, created_at DESC)
            """))
            await db.execute(text("""
                INSERT INTO notifications (user_id, title, body, type, priority, is_read, created_at)
                VALUES (:uid, :title, :body, :type, :priority, false, NOW())
            """), {"uid": user_id, "title": title, "body": body,
                   "type": notif_type, "priority": priority})
        except Exception as e2:
            logger.error(f"通知表创建失败: {e2}")

    # 2. 尝试微信推送 (不阻塞)
    try:
        await _try_wx_push(db, user_id, title, body, notif_type)
    except Exception:
        pass  # 静默

    # 3. 高优先级/里程碑 → 教练审批队列
    if priority == "high" or notif_type == "milestone":
        try:
            await _enqueue_coach_push(db, user_id, title, body, notif_type)
        except Exception:
            pass


async def _try_wx_push(
    db: AsyncSession, user_id: int,
    title: str, body: str, notif_type: str,
):
    """尝试通过 wx_gateway 推送微信模板消息"""
    result = await db.execute(
        text("SELECT wx_openid, preferred_channel FROM users WHERE id = :uid"),
        {"uid": user_id}
    )
    user = result.mappings().first()
    if not user or not user.get("wx_openid"):
        return
    if user.get("preferred_channel") not in (None, "wechat", "wx", "app"):
        return

    try:
        from gateway.wx_gateway import send_template_message
        template_map = {
            "morning_task": "daily_task_reminder",
            "evening_reminder": "daily_task_reminder",
            "reconnect": "care_message",
            "milestone": "achievement_notice",
        }
        await send_template_message(
            openid=user["wx_openid"],
            template_id=template_map.get(notif_type, "general_notice"),
            data={
                "title": {"value": title},
                "content": {"value": body[:200]},
                "time": {"value": datetime.now().strftime("%Y-%m-%d %H:%M")},
            }
        )
        logger.info(f"微信推送成功: user={user_id}, type={notif_type}")
    except ImportError:
        pass  # wx_gateway 未部署
    except Exception as e:
        logger.debug(f"微信推送失败: {e}")


async def _enqueue_coach_push(
    db: AsyncSession, user_id: int,
    title: str, body: str, notif_type: str,
):
    """写入教练推送审批队列 (遵循推送审批网关)"""
    try:
        coach_result = await db.execute(
            text("SELECT coach_id FROM coach_bindings WHERE student_id = :uid AND status = 'active' LIMIT 1"),
            {"uid": user_id}
        )
        coach = coach_result.mappings().first()
        if not coach:
            return

        import uuid
        await db.execute(text("""
            INSERT INTO coach_push_queue (id, coach_id, student_id, push_type, content, status, created_at)
            VALUES (:id, :cid, :uid, :type, :content, 'pending', NOW())
        """), {
            "id": f"push_{uuid.uuid4().hex[:12]}",
            "cid": coach["coach_id"], "uid": user_id,
            "type": notif_type, "content": f"{title}: {body}",
        })
    except Exception as e:
        logger.debug(f"教练推送队列写入跳过: {e}")


# ═══════════════════════════════════════════════════
# APScheduler 注册 (PATCH-4: 时间错开)
# ═══════════════════════════════════════════════════

def register_notification_jobs(scheduler, async_session_factory):
    """
    注册 3 个定时任务。
    时间: 07:15 / 10:15 / 20:15 (错开 program_push 的整点)
    """
    from core.redis_lock import with_redis_lock

    @with_redis_lock("scheduler:morning_notification", ttl=120)
    async def job_morning():
        async with async_session_factory() as db:
            await send_morning_notifications(db)

    @with_redis_lock("scheduler:evening_reminder", ttl=120)
    async def job_evening():
        async with async_session_factory() as db:
            await send_evening_reminders(db)

    @with_redis_lock("scheduler:reconnect_reminder", ttl=120)
    async def job_reconnect():
        async with async_session_factory() as db:
            await send_reconnect_reminders(db)

    scheduler.add_job(job_morning, 'cron', hour=7, minute=15,
                      id='morning_notif', replace_existing=True)
    scheduler.add_job(job_evening, 'cron', hour=20, minute=15,
                      id='evening_notif', replace_existing=True)
    scheduler.add_job(job_reconnect, 'cron', hour=10, minute=15,
                      id='reconnect_notif', replace_existing=True)

    logger.info("✅ notification_agent 3个定时任务已注册 (07:15/10:15/20:15)")


# ═══════════════════════════════════════════════════
# 通知查询 API
# ═══════════════════════════════════════════════════

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

notif_router = APIRouter(prefix="/api/v1", tags=["notifications"])


class NotificationItem(BaseModel):
    id: int
    title: str
    body: str
    type: str
    priority: str
    is_read: bool
    created_at: str


class NotificationsResponse(BaseModel):
    items: list[NotificationItem]
    unread_count: int


@notif_router.get("/notifications", response_model=NotificationsResponse)
async def get_notifications(
    limit: int = Query(20, ge=1, le=50),
    unread_only: bool = Query(False),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id
    where = "user_id = :uid" + (" AND is_read = false" if unread_only else "")

    try:
        rows = (await db.execute(text(f"""
            SELECT id, title, body, type, priority, is_read, created_at
            FROM notifications WHERE {where} ORDER BY created_at DESC LIMIT :lim
        """), {"uid": user_id, "lim": limit})).mappings().all()
    except Exception:
        rows = []

    items = [
        NotificationItem(
            id=r["id"], title=r["title"] or "", body=r["body"] or "",
            type=r["type"] or "", priority=r["priority"] or "normal",
            is_read=r["is_read"],
            created_at=r["created_at"].isoformat() if r["created_at"] else "",
        )
        for r in rows
    ]

    try:
        unread = (await db.execute(
            text("SELECT COUNT(*) FROM notifications WHERE user_id = :uid AND is_read = false"),
            {"uid": user_id}
        )).scalar() or 0
    except Exception:
        unread = 0

    return NotificationsResponse(items=items, unread_count=unread)


@notif_router.post("/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("UPDATE notifications SET is_read = true WHERE id = :nid AND user_id = :uid"),
                     {"nid": notif_id, "uid": current_user.id})
    await db.commit()
    return {"success": True}
