"""
BHP Celery Application — api/worker.py
docker-compose.yml 已引用: celery -A api.worker.celery_app worker --loglevel=info
"""
import os, logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

_redis = os.getenv("REDIS_URL", "redis://redis:6379/0")
BROKER_URL  = os.getenv("CELERY_BROKER_URL",    _redis.rsplit("/",1)[0] + "/1")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", _redis.rsplit("/",1)[0] + "/2")

celery_app = Celery("bhp_worker", broker=BROKER_URL, backend=BACKEND_URL)

celery_app.config_from_object({
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "Asia/Shanghai",
    "enable_utc": False,
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 200,
    "result_expires": 3600,
    "include": [
        "api.tasks.scheduler_tasks",
        "api.tasks.governance_tasks",
        "api.tasks.event_tasks",
    ],
})

celery_app.conf.beat_schedule = {
    # === 13 migrated from core/scheduler.py ===
    "daily-task-generation":   {"task":"api.tasks.scheduler_tasks.daily_task_generation",   "schedule":crontab(hour=6,  minute=0)},
    "reminder-check":          {"task":"api.tasks.scheduler_tasks.reminder_check",          "schedule":60.0,  "options":{"expires":50}},
    "expired-task-cleanup":    {"task":"api.tasks.scheduler_tasks.expired_task_cleanup",    "schedule":crontab(hour=23, minute=0)},
    "process-approved-pushes": {"task":"api.tasks.scheduler_tasks.process_approved_pushes", "schedule":300.0, "options":{"expires":280}},
    "expire-stale-queue-items":{"task":"api.tasks.scheduler_tasks.expire_stale_queue_items","schedule":crontab(hour=6,  minute=0)},
    "knowledge-freshness":     {"task":"api.tasks.scheduler_tasks.knowledge_freshness_check","schedule":crontab(hour=7,  minute=0)},
    "program-advance-day":     {"task":"api.tasks.scheduler_tasks.program_advance_day",     "schedule":crontab(hour=0,  minute=0)},
    "program-push-morning":    {"task":"api.tasks.scheduler_tasks.program_push_morning",    "schedule":crontab(hour=9,  minute=0)},
    "program-push-noon":       {"task":"api.tasks.scheduler_tasks.program_push_noon",       "schedule":crontab(hour=11, minute=30)},
    "program-push-evening":    {"task":"api.tasks.scheduler_tasks.program_push_evening",    "schedule":crontab(hour=17, minute=30)},
    "program-batch-analysis":  {"task":"api.tasks.scheduler_tasks.program_batch_analysis",  "schedule":crontab(hour=23, minute=30)},
    "safety-daily-report":     {"task":"api.tasks.scheduler_tasks.safety_daily_report",     "schedule":crontab(hour=2,  minute=0)},
    "agent-metrics-aggregate": {"task":"api.tasks.scheduler_tasks.agent_metrics_aggregate", "schedule":crontab(hour=1,  minute=0)},
    # === 3 new governance (cron) ===
    "governance-health-check": {"task":"api.tasks.governance_tasks.governance_health_check","schedule":crontab(hour=23, minute=30)},
    "coach-challenge-7d-push": {"task":"api.tasks.governance_tasks.coach_challenge_7d_push","schedule":crontab(hour=9,  minute=0)},
    "expert-program-14d-push": {"task":"api.tasks.governance_tasks.expert_program_14d_push","schedule":crontab(hour=0,  minute=5)},
    # promotion_ceremony 不在 Beat — 事件驱动 .delay()
}

logger.info("BHP Celery | broker=%s | %d beat tasks", BROKER_URL, len(celery_app.conf.beat_schedule))
