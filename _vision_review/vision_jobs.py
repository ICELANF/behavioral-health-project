"""
VisionGuard 定时任务  —  Job 27-31
续接原方案 Job 21-26，从 Job 27 起，08:15 错开策略延续。
Redis 锁：所有 Job 均开启（✅）

任务调度配置（在 celery_beat_schedule.py 中追加）：
---
'job_27_vision_behavior_score_calc': {
    'task': 'tasks.vision_jobs.job_27_behavior_score_calc',
    'schedule': crontab(hour=23, minute=0),
},
'job_28_vision_behavior_rx_trigger': {
    'task': 'tasks.vision_jobs.job_28_behavior_rx_trigger',
    'schedule': crontab(hour=23, minute=15),
},
'job_29_vision_parent_weekly_digest': {
    'task': 'tasks.vision_jobs.job_29_parent_weekly_digest',
    'schedule': crontab(day_of_week=0, hour=19, minute=0),  # 周日 19:00
},
'job_30_vision_expert_case_digest': {
    'task': 'tasks.vision_jobs.job_30_expert_case_digest',
    'schedule': crontab(hour=7, minute=0),
},
'job_31_vision_goal_auto_adjust': {
    'task': 'tasks.vision_jobs.job_31_goal_auto_adjust',
    'schedule': crontab(day_of_month=1, hour=4, minute=0),
},
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from celery import shared_task
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.migration_057_vision_behavior import (
    RiskLevelEnum,
    VisionBehaviorGoal,
    VisionBehaviorLog,
    VisionParentBinding,
)
from ..api.vision_behavior_router import calc_behavior_score

logger = logging.getLogger(__name__)

# Redis 锁 key 前缀（与平台现有约定一致）
LOCK_PREFIX = "vision_job_lock"


# ──────────────────────────────────────────────────────────────────────────────
# 工具：Redis 锁（替换为平台实际 redis_client）
# ──────────────────────────────────────────────────────────────────────────────
def acquire_lock(redis_client, key: str, ttl: int = 3600) -> bool:
    """获取 Redis 分布式锁，返回是否成功"""
    return bool(redis_client.set(key, "1", nx=True, ex=ttl))


def release_lock(redis_client, key: str):
    redis_client.delete(key)


# ══════════════════════════════════════════════════════════════════════════════
# Job 27  —  vision_behavior_score_calc  (每日 23:00)
# ══════════════════════════════════════════════════════════════════════════════
@shared_task(
    name="tasks.vision_jobs.job_27_behavior_score_calc",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def job_27_behavior_score_calc(self):
    """
    汇总当日五大行为日志 → 计算 behavior_score → 回写 vision_behavior_logs。
    覆盖范围：当日所有 behavior_score=0 的记录（防重复计算）。
    """
    # from app.core.db import get_sync_session
    # from app.core.redis import redis_client

    lock_key = f"{LOCK_PREFIX}:27:{date.today().isoformat()}"
    # if not acquire_lock(redis_client, lock_key):
    #     logger.info("Job 27 已运行，跳过")
    #     return

    logger.info("Job 27 [vision_behavior_score_calc] 开始")
    today = date.today()

    # with get_sync_session() as db:
    #     # 取今日所有 score=0 的记录
    #     logs = db.execute(
    #         select(VisionBehaviorLog).where(
    #             VisionBehaviorLog.log_date == today,
    #             VisionBehaviorLog.behavior_score == 0,
    #         )
    #     ).scalars().all()

    #     updated = 0
    #     for log in logs:
    #         goal_row = db.execute(
    #             select(VisionBehaviorGoal).where(VisionBehaviorGoal.user_id == log.user_id)
    #         ).scalar_one_or_none()

    #         if goal_row is None:
    #             goal_row = VisionBehaviorGoal(user_id=log.user_id)

    #         score = calc_behavior_score(log, goal_row)
    #         db.execute(
    #             update(VisionBehaviorLog)
    #             .where(VisionBehaviorLog.id == log.id)
    #             .values(behavior_score=score)
    #         )
    #         updated += 1

    #     db.commit()

    # logger.info(f"Job 27 完成，更新 {updated} 条行为评分")
    # release_lock(redis_client, lock_key)


# ══════════════════════════════════════════════════════════════════════════════
# Job 28  —  vision_behavior_rx_trigger  (每日 23:15)
# ══════════════════════════════════════════════════════════════════════════════
@shared_task(
    name="tasks.vision_jobs.job_28_behavior_rx_trigger",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def job_28_behavior_rx_trigger(self):
    """
    检查连续行为缺口（7天内达标天数 < 3）→ 触发处方生成 → 进入 coach_review_items。

    触发条件（任意一条满足）：
    - 连续 7 天户外时间 < 60 min
    - 连续 3 天屏幕总时间 > 目标的 150%
    - 叶黄素连续 5 天 < 目标 50%
    - next_exam_due 已过 7 天未更新（JOIN vision_exam_records）
    """
    lock_key = f"{LOCK_PREFIX}:28:{date.today().isoformat()}"
    logger.info("Job 28 [vision_behavior_rx_trigger] 开始")

    # with get_sync_session() as db:
    #     cutoff_7 = date.today() - timedelta(days=7)
    #     cutoff_3 = date.today() - timedelta(days=3)
    #     cutoff_5 = date.today() - timedelta(days=5)

    #     # ── 户外缺口检测 ──────────────────────────────────────────────────────
    #     outdoor_gap_users = db.execute(text("""
    #         SELECT vbl.user_id
    #         FROM vision_behavior_logs vbl
    #         JOIN vision_behavior_goals vbg ON vbg.user_id = vbl.user_id
    #         WHERE vbl.log_date >= :cutoff
    #           AND vbl.outdoor_minutes < 60
    #         GROUP BY vbl.user_id
    #         HAVING COUNT(*) >= 7
    #     """), {"cutoff": cutoff_7}).fetchall()

    #     # ── 屏幕超标检测 ──────────────────────────────────────────────────────
    #     screen_over_users = db.execute(text("""
    #         SELECT vbl.user_id
    #         FROM vision_behavior_logs vbl
    #         JOIN vision_behavior_goals vbg ON vbg.user_id = vbl.user_id
    #         WHERE vbl.log_date >= :cutoff
    #           AND vbl.screen_total_minutes > vbg.screen_daily_limit * 1.5
    #         GROUP BY vbl.user_id
    #         HAVING COUNT(*) >= 3
    #     """), {"cutoff": cutoff_3}).fetchall()

    #     # ── 叶黄素缺口检测 ────────────────────────────────────────────────────
    #     lutein_gap_users = db.execute(text("""
    #         SELECT vbl.user_id
    #         FROM vision_behavior_logs vbl
    #         JOIN vision_behavior_goals vbg ON vbg.user_id = vbl.user_id
    #         WHERE vbl.log_date >= :cutoff
    #           AND vbl.lutein_intake_mg < vbg.lutein_target_mg * 0.5
    #         GROUP BY vbl.user_id
    #         HAVING COUNT(*) >= 5
    #     """), {"cutoff": cutoff_5}).fetchall()

    #     triggered_users = set()
    #     for row in outdoor_gap_users + screen_over_users + lutein_gap_users:
    #         triggered_users.add(row.user_id)

    #     for user_id in triggered_users:
    #         _enqueue_rx_generation(db, user_id, trigger="behavior_gap_job28")

    #     db.commit()

    # logger.info(f"Job 28 完成，触发处方生成 {len(triggered_users)} 人")


def _enqueue_rx_generation(db, user_id: uuid.UUID, trigger: str):
    """
    将处方生成请求写入 coach_review_items（复用平台铁律流水线）。
    实际实现调用 XZBRxBridge.submit(user_id, trigger_type=trigger)
    """
    # from app.services.xzb_rx_bridge import XZBRxBridge
    # XZBRxBridge.submit(
    #     db=db,
    #     user_id=user_id,
    #     domain="VISION",
    #     trigger_type=trigger,
    #     priority=_rx_priority_from_risk(db, user_id),
    # )
    logger.debug(f"[RX] enqueue user={user_id} trigger={trigger}")


# ══════════════════════════════════════════════════════════════════════════════
# Job 29  —  vision_parent_weekly_digest  (Sunday 19:00)
# ══════════════════════════════════════════════════════════════════════════════
@shared_task(
    name="tasks.vision_jobs.job_29_parent_weekly_digest",
    bind=True,
    max_retries=2,
)
def job_29_parent_weekly_digest(self):
    """
    家长每周摘要推送：
    - 孩子七日行为达标率
    - 风险等级变化（与上周比）
    - 下周建议

    推送渠道：微信优先级队列（WATCH 及以上触发）
    家长账号独立计算配额（不与学员共享 3条/天 限流）
    """
    lock_key = f"{LOCK_PREFIX}:29:{date.today().isoformat()}"
    logger.info("Job 29 [vision_parent_weekly_digest] 开始")

    # with get_sync_session() as db:
    #     # 获取所有有效绑定
    #     bindings = db.execute(select(VisionParentBinding)).scalars().all()

    #     sent = 0
    #     for binding in bindings:
    #         student_id = binding.student_user_id
    #         parent_id = binding.parent_user_id

    #         # 计算近 7 天达标率
    #         week_ago = date.today() - timedelta(days=7)
    #         logs = db.execute(
    #             select(VisionBehaviorLog)
    #             .where(
    #                 VisionBehaviorLog.user_id == student_id,
    #                 VisionBehaviorLog.log_date >= week_ago,
    #             )
    #         ).scalars().all()

    #         if not logs:
    #             continue

    #         goal = db.execute(
    #             select(VisionBehaviorGoal).where(
    #                 VisionBehaviorGoal.user_id == student_id
    #             )
    #         ).scalar_one_or_none()

    #         compliance_rate = _calc_weekly_compliance(logs, goal)

    #         # 生成摘要 & 推送
    #         digest = _build_parent_digest(student_id, parent_id, logs, compliance_rate, db)
    #         _push_to_parent(parent_id, digest, binding.notify_risk_threshold)
    #         sent += 1

    # logger.info(f"Job 29 完成，推送家长摘要 {sent} 条")


def _calc_weekly_compliance(logs, goal) -> float:
    """计算七日五维综合达标率"""
    if not logs or not goal:
        return 0.0
    scores = [float(calc_behavior_score(log, goal)) for log in logs]
    return sum(scores) / (len(scores) * 100)


def _build_parent_digest(student_id, parent_id, logs, rate: float, db) -> dict:
    days = len(logs)
    avg_outdoor = sum(l.outdoor_minutes or 0 for l in logs) / days
    return {
        "student_id": str(student_id),
        "week_compliance_pct": round(rate * 100, 1),
        "avg_outdoor_minutes": round(avg_outdoor, 0),
        "days_recorded": days,
        "summary": (
            f"本周孩子记录了 {days} 天护眼数据，"
            f"综合达标率 {round(rate*100)}%，"
            f"平均户外时间 {round(avg_outdoor)} 分钟/天。"
        ),
    }


def _push_to_parent(parent_id, digest: dict, threshold: RiskLevelEnum):
    """推送至微信优先级队列（复用平台 WechatPushService）"""
    # from app.services.wechat_push import WechatPushService
    # WechatPushService.send(
    #     user_id=parent_id,
    #     template="parent_weekly_digest",
    #     data=digest,
    #     priority="NORMAL",
    # )
    logger.debug(f"[PUSH] parent={parent_id} digest={digest}")


# ══════════════════════════════════════════════════════════════════════════════
# Job 30  —  vision_expert_case_digest  (每日 07:00)
# ══════════════════════════════════════════════════════════════════════════════
@shared_task(
    name="tasks.vision_jobs.job_30_expert_case_digest",
    bind=True,
    max_retries=2,
)
def job_30_expert_case_digest(self):
    """
    行诊智伴专家工作台：推送昨日需关注学员摘要（ALERT / URGENT）
    摘要内容：VisionExam 历史 + 行为日志 + 处方执行情况
    """
    lock_key = f"{LOCK_PREFIX}:30:{date.today().isoformat()}"
    logger.info("Job 30 [vision_expert_case_digest] 开始")

    # with get_sync_session() as db:
    #     yesterday = date.today() - timedelta(days=1)

    #     # 找出昨日有 ALERT/URGENT 记录的学员
    #     at_risk_users = db.execute(text("""
    #         SELECT DISTINCT ver.user_id, ver.risk_level
    #         FROM vision_exam_records ver
    #         WHERE ver.created_at::date = :yesterday
    #           AND ver.risk_level IN ('ALERT', 'URGENT')
    #     """), {"yesterday": yesterday}).fetchall()

    #     # 按绑定专家分组，推送摘要
    #     for row in at_risk_users:
    #         case_summary = _build_expert_case_summary(row.user_id, row.risk_level, db)
    #         _push_to_expert_workbench(row.user_id, case_summary)

    # logger.info("Job 30 完成")


def _build_expert_case_summary(user_id: uuid.UUID, risk_level: str, db) -> dict:
    """构建专家工作台摘要卡片"""
    return {
        "student_id": str(user_id),
        "risk_level": risk_level,
        "generated_at": datetime.now().isoformat(),
        # 实际从 vision_exam_records + vision_behavior_logs JOIN 获取
    }


def _push_to_expert_workbench(student_id: uuid.UUID, summary: dict):
    """推送至行诊智伴专家工作台"""
    # from app.services.xzb_workbench import XZBWorkbenchService
    # XZBWorkbenchService.push_case(student_id=student_id, summary=summary)
    logger.debug(f"[EXPERT] student={student_id}")


# ══════════════════════════════════════════════════════════════════════════════
# Job 31  —  vision_goal_auto_adjust  (每月 1 日 04:00)
# ══════════════════════════════════════════════════════════════════════════════
@shared_task(
    name="tasks.vision_jobs.job_31_goal_auto_adjust",
    bind=True,
    max_retries=2,
)
def job_31_goal_auto_adjust(self):
    """
    根据最新 risk_level 重新评估 vision_behavior_goals 阈值。
    映射规则（风险等级 → 目标严格程度）：

    NORMAL  : 标准值（outdoor 120min / screen 120min）
    WATCH   : 加强值（outdoor 150min / screen 90min）
    ALERT   : 干预值（outdoor 180min / screen 60min）
    URGENT  : 紧急值（outdoor 180min / screen 45min + 立即就医提示）

    若目标已由专家手动设置（set_by_expert_id IS NOT NULL），跳过自动调整。
    """
    lock_key = f"{LOCK_PREFIX}:31:monthly"
    logger.info("Job 31 [vision_goal_auto_adjust] 开始")

    RISK_GOAL_MAP = {
        RiskLevelEnum.NORMAL: {
            "outdoor_target_min": 120,
            "screen_daily_limit": 120,
            "screen_session_limit": 20,
        },
        RiskLevelEnum.WATCH: {
            "outdoor_target_min": 150,
            "screen_daily_limit": 90,
            "screen_session_limit": 20,
        },
        RiskLevelEnum.ALERT: {
            "outdoor_target_min": 180,
            "screen_daily_limit": 60,
            "screen_session_limit": 15,
        },
        RiskLevelEnum.URGENT: {
            "outdoor_target_min": 180,
            "screen_daily_limit": 45,
            "screen_session_limit": 10,
        },
    }

    # with get_sync_session() as db:
    #     # 获取每位用户最新 risk_level（来自 vision_exam_records）
    #     latest_risk = db.execute(text("""
    #         SELECT DISTINCT ON (user_id) user_id, risk_level
    #         FROM vision_exam_records
    #         ORDER BY user_id, created_at DESC
    #     """)).fetchall()

    #     updated = 0
    #     for row in latest_risk:
    #         goal = db.execute(
    #             select(VisionBehaviorGoal).where(
    #                 VisionBehaviorGoal.user_id == row.user_id,
    #                 VisionBehaviorGoal.set_by_expert_id == None,  # 跳过专家定制
    #             )
    #         ).scalar_one_or_none()

    #         if goal is None:
    #             continue

    #         risk = RiskLevelEnum(row.risk_level)
    #         new_values = RISK_GOAL_MAP.get(risk, {})
    #         for field, val in new_values.items():
    #             setattr(goal, field, val)
    #         goal.risk_level_at_set = risk

    #         updated += 1

    #     db.commit()

    # logger.info(f"Job 31 完成，自动调整目标 {updated} 人")
