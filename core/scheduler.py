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

# === Celery Migration Switch (deploy_celery.sh) ===
import os as _os
_USE_CELERY = _os.getenv("USE_CELERY", "false").lower() == "true"
_DISABLE_APSCHEDULER = _os.getenv("DISABLE_APSCHEDULER", "false").lower() == "true"
# === End Switch ===


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


# ── Phase 4 反馈指标聚合定时任务 ────────────────────

@with_redis_lock("scheduler:agent_metrics_aggregate", ttl=600)
def agent_metrics_aggregate():
    """每天01:30聚合前一天Agent反馈指标"""
    from core.database import get_db_session
    from core.feedback_service import aggregate_daily_metrics

    try:
        with get_db_session() as db:
            count = aggregate_daily_metrics(db)
            db.commit()
            logger.info("[Scheduler] Agent指标聚合完成, agents=%d", count)
    except Exception as e:
        logger.error("[Scheduler] Agent指标聚合失败: %s", e)


# ── V005 安全日报定时任务 ──────────────────────────

@with_redis_lock("scheduler:safety_daily_report", ttl=600)
def safety_daily_report():
    """每天02:00统计前一天安全事件, 写入日报"""
    from datetime import timedelta
    from core.database import get_db_session
    from core.models import SafetyLog
    from sqlalchemy import func, and_

    try:
        with get_db_session() as db:
            now = datetime.now()
            yesterday_start = (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            yesterday_end = yesterday_start + timedelta(days=1)

            total = db.query(func.count(SafetyLog.id)).filter(
                and_(
                    SafetyLog.created_at >= yesterday_start,
                    SafetyLog.created_at < yesterday_end,
                )
            ).scalar() or 0

            by_severity = dict(
                db.query(SafetyLog.severity, func.count(SafetyLog.id)).filter(
                    and_(
                        SafetyLog.created_at >= yesterday_start,
                        SafetyLog.created_at < yesterday_end,
                    )
                ).group_by(SafetyLog.severity).all()
            )

            by_type = dict(
                db.query(SafetyLog.event_type, func.count(SafetyLog.id)).filter(
                    and_(
                        SafetyLog.created_at >= yesterday_start,
                        SafetyLog.created_at < yesterday_end,
                    )
                ).group_by(SafetyLog.event_type).all()
            )

            # 写入日报记录
            report = SafetyLog(
                user_id=None,
                event_type="daily_report",
                severity="low",
                input_text=None,
                output_text=None,
                filter_details={
                    "date": yesterday_start.strftime("%Y-%m-%d"),
                    "total_events": total,
                    "by_severity": by_severity,
                    "by_type": by_type,
                },
                resolved=True,
            )
            db.add(report)
            db.commit()

            logger.info(
                f"[Scheduler] 安全日报: {yesterday_start.strftime('%Y-%m-%d')} "
                f"total={total} severity={by_severity}"
            )
    except Exception as e:
        logger.error(f"[Scheduler] 安全日报生成失败: {e}")


# ── CR-15 治理健康度定期巡检 ──────────────────────────

@with_redis_lock("scheduler:governance_health_check", ttl=600)
def governance_health_check():
    """每6小时运行一次治理健康度全量检查(6维度)"""
    from core.database import get_db_session
    from core.governance_health_check import GovernanceHealthCheckService

    try:
        with get_db_session() as db:
            service = GovernanceHealthCheckService(db)
            report = service.run_full_check()
            logger.info(
                "[Scheduler] 治理健康度检查完成: overall=%s score=%.3f",
                report.overall_status.value, report.overall_score,
            )
    except Exception as e:
        logger.error("[Scheduler] 治理健康度检查失败: %s", e)


# ── CR-28 同道者生命周期更新 ──────────────────────────

@with_redis_lock("scheduler:companion_lifecycle_update", ttl=600)
def companion_lifecycle_update():
    """每天03:30更新同道关系生命周期状态(冷却/休眠/解除)"""
    from core.database import get_db_session
    from core.peer_tracking_service import PeerTrackingService

    try:
        with get_db_session() as db:
            service = PeerTrackingService(db)
            stats = service.update_lifecycle_states()
            logger.info(
                "[Scheduler] 同道者生命周期更新: cooling=%d dormant=%d dissolved=%d reactivated=%d",
                stats["cooling"], stats["dormant"],
                stats["dissolved"], stats["reactivated"],
            )
    except Exception as e:
        logger.error("[Scheduler] 同道者生命周期更新失败: %s", e)


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

    # ── V005 安全日报 ──
    scheduler.add_job(
        safety_daily_report,
        CronTrigger(hour=2, minute=0),
        id="safety_daily_report",
        name="安全事件日报",
        replace_existing=True,
    )

    # ── Phase 4 反馈指标聚合 ──
    scheduler.add_job(
        agent_metrics_aggregate,
        CronTrigger(hour=1, minute=30),
        id="agent_metrics_aggregate",
        name="Agent反馈指标聚合",
        replace_existing=True,
    )

    # ── CR-15 治理健康度巡检 (每6小时) ──
    scheduler.add_job(
        governance_health_check,
        IntervalTrigger(hours=6),
        id="governance_health_check",
        name="治理健康度巡检",
        replace_existing=True,
    )

    # ── CR-28 同道者生命周期更新 (每天03:30) ──
    scheduler.add_job(
        companion_lifecycle_update,
        CronTrigger(hour=3, minute=30),
        id="companion_lifecycle_update",
        name="同道者生命周期更新",
        replace_existing=True,
    )

    # ── R7 通知定时任务 (07:15/10:15/20:15, 错开 program_push 整点) ──
    try:
        from api.r7_notification_agent import register_notification_jobs
        from core.database import AsyncSessionLocal
        register_notification_jobs(scheduler, AsyncSessionLocal)
    except Exception as e:
        logger.warning(f"[Scheduler] R7 notification_agent 注册失败: {e}")

    # ── R8 上下文过期清理 (每天02:00) ──
    try:
        from api.r8_user_context import cleanup_expired_contexts
        from core.database import AsyncSessionLocal as _AsyncSessionLocal

        @with_redis_lock("scheduler:cleanup_contexts", ttl=60)
        async def job_cleanup_contexts():
            async with _AsyncSessionLocal() as db:
                await cleanup_expired_contexts(db)

        scheduler.add_job(
            job_cleanup_contexts,
            CronTrigger(hour=2, minute=0),
            id="cleanup_contexts",
            name="R8用户上下文过期清理",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] R8 context cleanup 注册失败: {e}")

    logger.info("[Scheduler] 定时任务调度器已配置 (含V004方案引擎+V005安全日报+Phase4指标聚合+CR15治理巡检+CR28同道生命周期+R7通知+R8上下文)")
    return scheduler
