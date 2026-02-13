"""13 个从 core/scheduler.py 迁移的定时任务 — 不改任何业务逻辑"""
import logging, importlib
from api.worker import celery_app
from api.tasks.db import get_sync_session, task_lock
logger = logging.getLogger(__name__)

def _call(fn, lock=False, ttl=60):
    if lock:
        with task_lock(fn, ttl=ttl) as acq:
            if not acq:
                logger.info("[%s] skipped — lock held", fn); return {"status":"skipped"}
            return _exec(fn)
    return _exec(fn)

def _exec(fn):
    mod = importlib.import_module("core.scheduler"); func = getattr(mod, fn)
    with get_sync_session() as db:
        try: r = func(db)
        except TypeError: r = func()
    logger.info("[%s] ok", fn); return {"status":"ok","func":fn}

# 11 Cron
@celery_app.task(name="api.tasks.scheduler_tasks.daily_task_generation",   bind=True, max_retries=2, default_retry_delay=60)
def daily_task_generation(self):
    try: return _call("daily_task_generation")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.expired_task_cleanup",    bind=True, max_retries=2, default_retry_delay=60)
def expired_task_cleanup(self):
    try: return _call("expired_task_cleanup")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.expire_stale_queue_items",bind=True, max_retries=2, default_retry_delay=60)
def expire_stale_queue_items(self):
    try: return _call("expire_stale_queue_items")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.knowledge_freshness_check",bind=True, max_retries=2, default_retry_delay=60)
def knowledge_freshness_check(self):
    try: return _call("knowledge_freshness_check")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.program_advance_day",     bind=True, max_retries=2, default_retry_delay=60)
def program_advance_day(self):
    try: return _call("program_advance_day")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.program_push_morning")
def program_push_morning(): return _call("program_push_morning")

@celery_app.task(name="api.tasks.scheduler_tasks.program_push_noon")
def program_push_noon(): return _call("program_push_noon")

@celery_app.task(name="api.tasks.scheduler_tasks.program_push_evening")
def program_push_evening(): return _call("program_push_evening")

@celery_app.task(name="api.tasks.scheduler_tasks.program_batch_analysis",  bind=True, max_retries=2, default_retry_delay=120)
def program_batch_analysis(self):
    try: return _call("program_batch_analysis")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.safety_daily_report",     bind=True, max_retries=2, default_retry_delay=60)
def safety_daily_report(self):
    try: return _call("safety_daily_report")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.agent_metrics_aggregate", bind=True, max_retries=2, default_retry_delay=60)
def agent_metrics_aggregate(self):
    try: return _call("agent_metrics_aggregate")
    except Exception as e: raise self.retry(exc=e)

# 2 高频 (加锁)
@celery_app.task(name="api.tasks.scheduler_tasks.reminder_check")
def reminder_check(): return _call("reminder_check", lock=True, ttl=50)

@celery_app.task(name="api.tasks.scheduler_tasks.process_approved_pushes")
def process_approved_pushes(): return _call("process_approved_pushes", lock=True, ttl=280)
