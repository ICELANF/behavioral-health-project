# -*- coding: utf-8 -*-
"""
Scheduler - 定时任务调度

使用 APScheduler 实现:
- daily_task_generation: 每天06:00为活跃用户生成今日微行动任务
- reminder_check: 每分钟查询到期提醒并推送
- expired_task_cleanup: 每天23:59将过期未完成任务标记为 expired
"""
from datetime import datetime, date, timedelta
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

    # ── R2 处方→每日任务生成 (06:15, 错开 daily_task_generation 06:00) ──
    try:
        from api.r2_scheduler_agent import run_daily_task_generation
        from core.database import AsyncSessionLocal as _R2Async

        @with_redis_lock("scheduler:prescription_task_generation", ttl=600)
        async def job_prescription_task_generation():
            async with _R2Async() as db:
                result = await run_daily_task_generation(db)
                logger.info(f"[Scheduler] R2 处方任务生成: {result}")

        scheduler.add_job(
            job_prescription_task_generation,
            CronTrigger(hour=6, minute=15),
            id="prescription_task_generation",
            name="R2处方→每日任务生成",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] R2 prescription_task_generation 注册失败: {e}")

    # ── Route 9: 信任分下降 + 参与度预警 (每天22:00) ──
    try:
        from core.database import AsyncSessionLocal as _R9Async

        @with_redis_lock("scheduler:trust_engagement_monitor", ttl=600)
        async def job_trust_engagement_monitor():
            from sqlalchemy import text as sa_text
            async with _R9Async() as db:
                # Users with trust_score < 0.3 AND inactive 3+ days AND have active Rx
                stmt = sa_text("""
                    SELECT u.id AS user_id, u.trust_score,
                           us.current_streak, us.last_checkin_date,
                           (u.profile->>'coach_id')::int AS coach_id
                    FROM users u
                    JOIN user_streaks us ON us.user_id = u.id
                    WHERE u.is_active = true
                      AND u.trust_score < 0.3
                      AND us.last_checkin_date < CURRENT_DATE - INTERVAL '3 days'
                      AND EXISTS (
                          SELECT 1 FROM behavior_prescriptions bp
                          WHERE bp.user_id = u.id AND bp.status = 'active'
                      )
                """)
                try:
                    rows = (await db.execute(stmt)).mappings().all()
                except Exception:
                    rows = []

                flagged = 0
                for row in rows:
                    uid, coach_id = row["user_id"], row["coach_id"]
                    trust = row["trust_score"] or 0.0
                    days = (date.today() - row["last_checkin_date"]).days if row["last_checkin_date"] else 0

                    # Notify user
                    try:
                        await db.execute(sa_text("""
                            INSERT INTO notifications
                              (user_id, title, body, type, priority, is_read, created_at)
                            VALUES (:uid, '我们注意到了变化',
                              '最近几天参与度有所下降，没关系，随时可以回来，我们在这里支持您。',
                              'trust_decline', 'normal', false, NOW())
                        """), {"uid": uid})
                    except Exception:
                        pass

                    # Enqueue coach alert (if coach assigned)
                    if coach_id:
                        try:
                            await db.execute(sa_text("""
                                INSERT INTO coach_push_queue
                                  (coach_id, student_id, source_type, title, content,
                                   priority, status, created_at)
                                VALUES (:cid, :uid, 'trust_decline',
                                  '学员参与度下降预警',
                                  :content, 'high', 'pending', NOW())
                            """), {
                                "cid": coach_id, "uid": uid,
                                "content": f"信任分 {trust:.2f}，已 {days} 天未打卡，建议主动关怀",
                            })
                            flagged += 1
                        except Exception:
                            pass

                if rows:
                    await db.commit()
                logger.info(f"[Scheduler] 信任预警: {len(rows)} 低信任用户, {flagged} 教练通知")

        scheduler.add_job(
            job_trust_engagement_monitor,
            CronTrigger(hour=22, minute=0),
            id="trust_engagement_monitor",
            name="信任分下降+参与度预警",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] trust_engagement_monitor 注册失败: {e}")

    # ── Route 10: 教练自动升级预警 (每天08:00) ──
    try:
        from core.database import AsyncSessionLocal as _R10Async

        @with_redis_lock("scheduler:coach_auto_escalation", ttl=600)
        async def job_coach_auto_escalation():
            from sqlalchemy import text as sa_text
            async with _R10Async() as db:
                stmt = sa_text("""
                    SELECT u.id AS user_id,
                           (u.profile->>'coach_id')::int AS coach_id,
                           us.last_checkin_date, u.trust_score,
                           COUNT(bp.id) AS rx_count
                    FROM users u
                    JOIN user_streaks us ON us.user_id = u.id
                    JOIN behavior_prescriptions bp
                        ON bp.user_id = u.id AND bp.status = 'active'
                    WHERE u.is_active = true
                      AND u.profile->>'coach_id' IS NOT NULL
                      AND us.last_checkin_date < CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY u.id, us.last_checkin_date, u.trust_score
                """)
                try:
                    rows = (await db.execute(stmt)).mappings().all()
                except Exception:
                    rows = []

                escalated = 0
                for row in rows:
                    uid, cid = row["user_id"], row["coach_id"]
                    if not cid:
                        continue
                    days = (date.today() - row["last_checkin_date"]).days if row["last_checkin_date"] else 999
                    trust = row["trust_score"] or 0.0

                    # Dedup: skip if pending escalation exists within 7 days
                    try:
                        dup = await db.execute(sa_text("""
                            SELECT 1 FROM coach_push_queue
                            WHERE student_id = :uid AND source_type = 'auto_escalation'
                              AND status = 'pending'
                              AND created_at > CURRENT_DATE - INTERVAL '7 days'
                            LIMIT 1
                        """), {"uid": uid})
                        if dup.first():
                            continue
                    except Exception:
                        pass

                    try:
                        await db.execute(sa_text("""
                            INSERT INTO coach_push_queue
                              (coach_id, student_id, source_type, title, content,
                               priority, status, created_at)
                            VALUES (:cid, :uid, 'auto_escalation',
                              :title, :content, 'high', 'pending', NOW())
                        """), {
                            "cid": cid, "uid": uid,
                            "title": f"学员失联预警 ({days}天未打卡)",
                            "content": f"已 {days} 天未打卡，信任分 {trust:.2f}，"
                                       f"有 {row['rx_count']} 个活跃处方未执行，建议主动联系。",
                        })
                        escalated += 1
                    except Exception:
                        pass

                if escalated:
                    await db.commit()
                logger.info(f"[Scheduler] 教练自动升级: {len(rows)} 候选, {escalated} 升级")

        scheduler.add_job(
            job_coach_auto_escalation,
            CronTrigger(hour=8, minute=0),
            id="coach_auto_escalation",
            name="教练自动升级预警",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] coach_auto_escalation 注册失败: {e}")

    # ── P5B: 每日分析聚合 (每天03:00) ──
    try:
        from core.database import AsyncSessionLocal as _P5bAsync

        @with_redis_lock("scheduler:analytics_daily_aggregate", ttl=600)
        async def job_analytics_daily_aggregate():
            from sqlalchemy import text as sa_text
            async with _P5bAsync() as db:
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                try:
                    # DAU
                    dau_r = await db.execute(sa_text(
                        "SELECT COUNT(DISTINCT user_id) FROM user_activity_logs WHERE created_at::date = :d"
                    ), {"d": yesterday})
                    dau = dau_r.scalar() or 0

                    # New users
                    new_r = await db.execute(sa_text(
                        "SELECT COUNT(*) FROM users WHERE created_at::date = :d"
                    ), {"d": yesterday})
                    new_users = new_r.scalar() or 0

                    # Active growers (role > OBSERVER with activity)
                    ag_r = await db.execute(sa_text("""
                        SELECT COUNT(DISTINCT u.id) FROM users u
                        JOIN user_activity_logs ual ON ual.user_id = u.id
                        WHERE ual.created_at::date = :d AND u.role::text != 'OBSERVER'
                    """), {"d": yesterday})
                    active_growers = ag_r.scalar() or 0

                    # Conversion rate (growers+ / total)
                    total_r = await db.execute(sa_text("SELECT COUNT(*) FROM users WHERE is_active = true"))
                    total = total_r.scalar() or 1
                    non_obs_r = await db.execute(sa_text(
                        "SELECT COUNT(*) FROM users WHERE is_active = true AND role::text != 'OBSERVER'"
                    ))
                    non_obs = non_obs_r.scalar() or 0
                    conversion_rate = round(non_obs / total, 4) if total else 0.0

                    # 7-day retention
                    d7_ago = (date.today() - timedelta(days=8)).isoformat()
                    d7_users_r = await db.execute(sa_text(
                        "SELECT COUNT(DISTINCT user_id) FROM user_activity_logs WHERE created_at::date = :d"
                    ), {"d": d7_ago})
                    d7_users = d7_users_r.scalar() or 0
                    if d7_users:
                        retained_r = await db.execute(sa_text("""
                            SELECT COUNT(DISTINCT ual1.user_id) FROM user_activity_logs ual1
                            WHERE ual1.created_at::date = :d1
                              AND ual1.user_id IN (
                                SELECT DISTINCT user_id FROM user_activity_logs WHERE created_at::date = :d0
                              )
                        """), {"d0": d7_ago, "d1": yesterday})
                        retained = retained_r.scalar() or 0
                        retention_7d = round(retained / d7_users, 4)
                    else:
                        retention_7d = 0.0

                    # Total events
                    ev_r = await db.execute(sa_text(
                        "SELECT COUNT(*) FROM user_activity_logs WHERE created_at::date = :d"
                    ), {"d": yesterday})
                    total_events = ev_r.scalar() or 0

                    # Chat messages
                    chat_r = await db.execute(sa_text(
                        "SELECT COUNT(*) FROM user_activity_logs WHERE created_at::date = :d AND activity_type IN ('chat', 'chat_message')"
                    ), {"d": yesterday})
                    total_chat = chat_r.scalar() or 0

                    # AI response avg ms
                    ai_r = await db.execute(sa_text("""
                        SELECT AVG(CAST(detail->>'response_ms' AS FLOAT))
                        FROM user_activity_logs
                        WHERE created_at::date = :d AND detail->>'response_ms' IS NOT NULL
                    """), {"d": yesterday})
                    ai_avg = ai_r.scalar() or 0.0

                    # Upsert
                    await db.execute(sa_text("""
                        INSERT INTO analytics_daily
                            (date, dau, new_users, active_growers, conversion_rate,
                             retention_7d, avg_tasks_completed, avg_session_minutes,
                             ai_response_avg_ms, total_events, total_chat_messages)
                        VALUES (:d, :dau, :nu, :ag, :cr, :r7, 0.0, 0.0, :ai, :te, :tc)
                        ON CONFLICT (date) DO UPDATE SET
                            dau = EXCLUDED.dau, new_users = EXCLUDED.new_users,
                            active_growers = EXCLUDED.active_growers,
                            conversion_rate = EXCLUDED.conversion_rate,
                            retention_7d = EXCLUDED.retention_7d,
                            ai_response_avg_ms = EXCLUDED.ai_response_avg_ms,
                            total_events = EXCLUDED.total_events,
                            total_chat_messages = EXCLUDED.total_chat_messages
                    """), {
                        "d": yesterday, "dau": dau, "nu": new_users, "ag": active_growers,
                        "cr": conversion_rate, "r7": retention_7d,
                        "ai": round(ai_avg, 1), "te": total_events, "tc": total_chat,
                    })
                    await db.commit()
                    logger.info(f"[Scheduler] 分析聚合完成: date={yesterday} DAU={dau} events={total_events}")
                except Exception as e:
                    logger.warning(f"[Scheduler] 分析聚合失败: {e}")

        scheduler.add_job(
            job_analytics_daily_aggregate,
            CronTrigger(hour=3, minute=0),
            id="analytics_daily_aggregate",
            name="P5B每日分析聚合",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] analytics_daily_aggregate 注册失败: {e}")

    # ── P5B: 周报生成 (每周一07:00) ──
    try:
        from core.database import AsyncSessionLocal as _P5bWeekly

        @with_redis_lock("scheduler:weekly_report_generation", ttl=600)
        async def job_weekly_report_generation():
            from sqlalchemy import text as sa_text
            async with _P5bWeekly() as db:
                end_date = date.today() - timedelta(days=1)
                start_date = end_date - timedelta(days=6)
                try:
                    result = await db.execute(sa_text("""
                        SELECT date::text, dau, new_users, conversion_rate, retention_7d,
                               total_events, total_chat_messages
                        FROM analytics_daily
                        WHERE date BETWEEN :s AND :e ORDER BY date
                    """), {"s": start_date, "e": end_date})
                    rows = result.mappings().all()

                    if not rows:
                        logger.info("[Scheduler] 周报: 无数据")
                        return

                    avg_dau = sum(r["dau"] or 0 for r in rows) // len(rows)
                    total_new = sum(r["new_users"] or 0 for r in rows)
                    avg_conv = round(sum(r["conversion_rate"] or 0 for r in rows) / len(rows), 3)

                    # Try send email to admin users
                    try:
                        from gateway.channels.email_gateway import send_email, is_configured
                        if is_configured():
                            admin_r = await db.execute(sa_text(
                                "SELECT email FROM users WHERE role::text = 'ADMIN' AND is_active = true"
                            ))
                            for admin in admin_r.mappings().all():
                                await send_email(
                                    to=admin["email"],
                                    subject=f"行健平台周报 {start_date} ~ {end_date}",
                                    body_html=f"""
                                    <h2>行健平台周报</h2>
                                    <p>日均活跃: {avg_dau} | 新增用户: {total_new} | 转化率: {avg_conv:.1%}</p>
                                    <p>详细报表请登录管理后台查看</p>
                                    """,
                                )
                    except Exception:
                        pass

                    logger.info(f"[Scheduler] 周报生成: {start_date}~{end_date} DAU={avg_dau}")
                except Exception as e:
                    logger.warning(f"[Scheduler] 周报生成失败: {e}")

        scheduler.add_job(
            job_weekly_report_generation,
            CronTrigger(day_of_week="mon", hour=7, minute=0),
            id="weekly_report_generation",
            name="P5B周报生成",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] weekly_report_generation 注册失败: {e}")

    # ── P6B 用户行为周报 (每周日 21:00) ──
    try:
        from core.database import AsyncSessionLocal as _P6bWeekly

        @with_redis_lock("scheduler:user_weekly_report", ttl=900)
        async def job_user_weekly_report():
            from api.weekly_report_service import generate_all_reports
            today = date.today()
            ws = today - timedelta(days=today.weekday() + 7)  # 上周一
            we = ws + timedelta(days=6)
            async with _P6bWeekly() as db:
                await generate_all_reports(db, ws, we)

        scheduler.add_job(
            job_user_weekly_report,
            CronTrigger(day_of_week="sun", hour=21, minute=0),
            id="user_weekly_report",
            name="P6B用户行为周报",
            replace_existing=True,
        )
    except Exception as e:
        logger.warning(f"[Scheduler] user_weekly_report 注册失败: {e}")

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

    logger.info("[Scheduler] 定时任务调度器已配置 (含V004+V005+Phase4+CR15+CR28+R2处方+R9信任预警+R10教练升级+R7通知+R8上下文)")
    return scheduler
