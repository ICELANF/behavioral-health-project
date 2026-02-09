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
from core.redis_lock import with_redis_lock

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not installed, scheduled tasks disabled")


@with_redis_lock("scheduler:daily_task_generation", ttl=600)
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


@with_redis_lock("scheduler:reminder_check", ttl=60)
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


@with_redis_lock("scheduler:expired_task_cleanup", ttl=300)
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


@with_redis_lock("scheduler:process_approved_pushes", ttl=300)
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


@with_redis_lock("scheduler:expire_stale_queue_items", ttl=300)
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


@with_redis_lock("scheduler:knowledge_freshness_check", ttl=300)
def knowledge_freshness_check():
    """每天07:00检查过期知识文档并降权"""
    from core.database import get_db_session
    from core.knowledge.document_service import handle_expired_documents

    try:
        with get_db_session() as db:
            count = handle_expired_documents(db)
            if count:
                logger.info(f"[Scheduler] 知识库过期降权: {count} 篇")
    except Exception as e:
        logger.error(f"[Scheduler] 知识库过期检查失败: {e}")


# ── V004 方案引擎定时任务 ──────────────────────────

@with_redis_lock("scheduler:program_advance_day", ttl=600)
def program_advance_day():
    """每天00:05推进所有active enrollment天数"""
    from core.database import get_db_session
    from core.program_service import ProgramService

    try:
        with get_db_session() as db:
            service = ProgramService(db)
            result = service.scheduled_advance_day()
            logger.info(f"[Scheduler] 方案天数推进: {result}")
    except Exception as e:
        logger.error(f"[Scheduler] 方案天数推进失败: {e}")


def _program_push(slot: str):
    """方案推送通用函数"""
    from core.database import get_db_session
    from core.program_service import ProgramService

    try:
        with get_db_session() as db:
            service = ProgramService(db)
            result = service.scheduled_send_pushes(slot)
            logger.info(f"[Scheduler] 方案推送[{slot}]: {result}")
    except Exception as e:
        logger.error(f"[Scheduler] 方案推送[{slot}]失败: {e}")


@with_redis_lock("scheduler:program_push_morning", ttl=300)
def program_push_morning():
    """每天09:00发送方案早间推送"""
    _program_push("morning")


@with_redis_lock("scheduler:program_push_noon", ttl=300)
def program_push_noon():
    """每天11:30发送方案午间推送"""
    _program_push("noon")


@with_redis_lock("scheduler:program_push_evening", ttl=300)
def program_push_evening():
    """每天17:30发送方案晚间推送"""
    _program_push("evening")


@with_redis_lock("scheduler:program_batch_analysis", ttl=600)
def program_batch_analysis():
    """每天23:00批量更新行为特征"""
    from core.database import get_db_session
    from core.program_service import ProgramService
    from sqlalchemy import text

    try:
        with get_db_session() as db:
            service = ProgramService(db)
            enrollments = db.execute(text(
                "SELECT id, user_id FROM program_enrollments WHERE status = 'active'"
            )).fetchall()
            updated = 0
            for e in enrollments:
                try:
                    service._update_behavior_profile(str(e.id), e.user_id, None, None)
                    updated += 1
                except Exception as ex:
                    logger.warning(f"方案行为分析失败 {e.id}: {ex}")
            db.commit()
            logger.info(f"[Scheduler] 方案行为分析: {updated}/{len(enrollments)}")
    except Exception as e:
        logger.error(f"[Scheduler] 方案批量分析失败: {e}")


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

    # 每天 07:00 检查知识文档过期并降权
    scheduler.add_job(
        knowledge_freshness_check,
        CronTrigger(hour=7, minute=0),
        id="knowledge_freshness_check",
        name="知识库过期降权检查",
        replace_existing=True,
    )

    # ── V004 方案引擎: 5个定时任务 ──

    # 每天 00:05 推进方案天数
    scheduler.add_job(
        program_advance_day,
        CronTrigger(hour=0, minute=5),
        id="program_advance_day",
        name="方案天数推进",
        replace_existing=True,
    )

    # 每天 09:00 方案早间推送
    scheduler.add_job(
        program_push_morning,
        CronTrigger(hour=9, minute=0),
        id="program_push_morning",
        name="方案早间推送",
        replace_existing=True,
    )

    # 每天 11:30 方案午间推送
    scheduler.add_job(
        program_push_noon,
        CronTrigger(hour=11, minute=30),
        id="program_push_noon",
        name="方案午间推送",
        replace_existing=True,
    )

    # 每天 17:30 方案晚间推送
    scheduler.add_job(
        program_push_evening,
        CronTrigger(hour=17, minute=30),
        id="program_push_evening",
        name="方案晚间推送",
        replace_existing=True,
    )

    # 每天 23:00 批量行为分析
    scheduler.add_job(
        program_batch_analysis,
        CronTrigger(hour=23, minute=0),
        id="program_batch_analysis",
        name="方案行为批量分析",
        replace_existing=True,
    )

    logger.info("[Scheduler] 定时任务调度器已配置 (含V004方案引擎)")
    return scheduler
