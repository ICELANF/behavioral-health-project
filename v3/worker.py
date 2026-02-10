"""
Celery Worker 配置
放置: api/worker.py

后台任务:
  - 知识库增量更新
  - LLM 调用日志持久化
  - 周报生成
  - 定时评估提醒
"""
import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "bhp",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=300,         # 5 分钟超时
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)


# ── 定时任务 ──
celery_app.conf.beat_schedule = {
    # 每天凌晨 2 点: 持久化 LLM 调用日志
    "flush-llm-logs": {
        "task": "api.tasks.flush_llm_logs",
        "schedule": crontab(hour=2, minute=0),
    },
    # 每周一 8 点: 为所有活跃用户生成周报
    "weekly-reviews": {
        "task": "api.tasks.generate_weekly_reviews",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
}


# ── 任务注册 ──

@celery_app.task(name="api.tasks.flush_llm_logs")
def flush_llm_logs():
    """将内存中的 LLM 调用日志写入数据库"""
    # TODO: 从 CoachAgent._conversation_log 读取并写入 llm_call_logs 表
    return {"status": "ok", "message": "placeholder"}


@celery_app.task(name="api.tasks.generate_weekly_reviews")
def generate_weekly_reviews():
    """批量生成周度效果报告"""
    # TODO: 查询活跃用户, 调用 generate_weekly_review
    return {"status": "ok", "message": "placeholder"}


@celery_app.task(name="api.tasks.load_knowledge_file")
def load_knowledge_file(filepath: str, doc_type: str = "spec"):
    """异步加载知识库文件 (大文件不阻塞 API)"""
    from v3.dependencies import get_knowledge_loader
    loader = get_knowledge_loader()
    return loader.load_file(filepath, doc_type=doc_type)
