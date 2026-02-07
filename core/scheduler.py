# -*- coding: utf-8 -*-
"""
Scheduler - 定时任务调度

使用 APScheduler 实现:
- daily_task_generation: 每天06:00为活跃用户生成今日微行动任务
- reminder_check: 每分钟查询到期提醒并推送
- expired_task_cleanup: 每天23:59将过期未完成任务标记为 expired
"""
from datetime import datetime
from loguru import logger

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not installed, scheduled tasks disabled")


def daily_task_generation():
    """每天06:00为所有活跃用户生成今日微行动任务"""
    from core.database import get_db_session
    from core.models import User
    from core.micro_action_service import MicroActionTaskService

    service = MicroActionTaskService()

    try:
        with get_db_session() as db:
            active_users = (
                db.query(User)
                .filter(User.is_active == True)
                .all()
            )
            count = 0
            for user in active_users:
                try:
                    tasks = service.generate_daily_tasks(db, user.id)
                    if tasks:
                        count += 1
                except Exception as e:
                    logger.warning(f"为用户 {user.id} 生成任务失败: {e}")

            logger.info(f"[Scheduler] 每日任务生成完成: {count}/{len(active_users)} 用户")
    except Exception as e:
        logger.error(f"[Scheduler] 每日任务生成失败: {e}")


def reminder_check():
    """每分钟查询到期提醒并触发"""
    from core.database import get_db_session
    from core.reminder_service import ReminderService

    service = ReminderService()

    try:
        with get_db_session() as db:
            due_reminders = service.get_due_reminders(db)
            for reminder in due_reminders:
                try:
                    service.fire_reminder(db, reminder)
                except Exception as e:
                    logger.warning(f"触发提醒失败 id={reminder.id}: {e}")

            if due_reminders:
                logger.info(f"[Scheduler] 触发 {len(due_reminders)} 条提醒")
    except Exception as e:
        logger.error(f"[Scheduler] 提醒检查失败: {e}")


def expired_task_cleanup():
    """每天23:59将过期未完成任务标记为 expired"""
    from core.database import get_db_session
    from core.micro_action_service import MicroActionTaskService

    service = MicroActionTaskService()

    try:
        with get_db_session() as db:
            count = service.expire_overdue_tasks(db)
            logger.info(f"[Scheduler] 过期任务清理: {count} 条")
    except Exception as e:
        logger.error(f"[Scheduler] 过期任务清理失败: {e}")


def process_approved_pushes():
    """每5分钟投递已审批且到时的推送"""
    from core.database import get_db_session
    from core import coach_push_queue_service as queue_svc

    try:
        with get_db_session() as db:
            count = queue_svc.process_due_approved(db)
            if count:
                logger.info(f"[Scheduler] 定时投递推送: {count} 条")
    except Exception as e:
        logger.error(f"[Scheduler] 定时投递推送失败: {e}")


def expire_stale_queue_items():
    """每天06:30清理72h超时未审批的推送条目"""
    from core.database import get_db_session
    from core import coach_push_queue_service as queue_svc

    try:
        with get_db_session() as db:
            count = queue_svc.expire_stale_items(db, hours=72)
            logger.info(f"[Scheduler] 过期推送清理: {count} 条")
    except Exception as e:
        logger.error(f"[Scheduler] 过期推送清理失败: {e}")


def setup_scheduler() -> "AsyncIOScheduler | None":
    """
    配置并返回调度器

    在 FastAPI lifespan 中调用:
        scheduler = setup_scheduler()
        if scheduler:
            scheduler.start()
    """
    if not HAS_APSCHEDULER:
        logger.warning("APScheduler 未安装，跳过调度器配置")
        return None

    scheduler = AsyncIOScheduler()

    # 每天 06:00 生成今日微行动任务
    scheduler.add_job(
        daily_task_generation,
        CronTrigger(hour=6, minute=0),
        id="daily_task_generation",
        name="每日微行动任务生成",
        replace_existing=True,
    )

    # 每分钟检查到期提醒
    scheduler.add_job(
        reminder_check,
        IntervalTrigger(minutes=1),
        id="reminder_check",
        name="提醒检查",
        replace_existing=True,
    )

    # 每天 23:59 清理过期任务
    scheduler.add_job(
        expired_task_cleanup,
        CronTrigger(hour=23, minute=59),
        id="expired_task_cleanup",
        name="过期任务清理",
        replace_existing=True,
    )

    # 每 5 分钟投递已审批且到时的推送
    scheduler.add_job(
        process_approved_pushes,
        IntervalTrigger(minutes=5),
        id="process_approved_pushes",
        name="投递已审批推送",
        replace_existing=True,
    )

    # 每天 06:30 清理 72h 超时未审批条目
    scheduler.add_job(
        expire_stale_queue_items,
        CronTrigger(hour=6, minute=30),
        id="expire_stale_queue_items",
        name="过期推送清理",
        replace_existing=True,
    )

    logger.info("[Scheduler] 定时任务调度器已配置")
    return scheduler
