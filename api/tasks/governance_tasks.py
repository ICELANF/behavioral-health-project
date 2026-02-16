"""4 个新增治理任务 — Celery async tasks for governance subsystem"""
import logging
from datetime import date
from api.worker import celery_app
from api.tasks.db import get_sync_session
logger = logging.getLogger(__name__)

@celery_app.task(name="api.tasks.governance_tasks.governance_health_check", bind=True, max_retries=2, default_retry_delay=120)
def governance_health_check(self):
    """每日治理健康检查 — 统计违规/合规数据"""
    try:
        with get_sync_session() as db:
            logger.info("[governance_health_check] %s", date.today())
            # Phase 1: 返回空结果 (后续接入 GovernanceViolation 统计)
            return {"date": str(date.today()), "total": 0}
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.governance_tasks.coach_challenge_7d_push", bind=True, max_retries=2, default_retry_delay=60)
def coach_challenge_7d_push(self):
    """每周教练挑战推送 — 扫描7天未活跃教练"""
    try:
        with get_sync_session() as db:
            logger.info("[coach_challenge_7d_push] scanning")
            # Phase 1: 返回空结果 (后续接入 coach_push_queue)
            return {"status": "ok", "processed": 0}
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.governance_tasks.expert_program_14d_push", bind=True, max_retries=2, default_retry_delay=60)
def expert_program_14d_push(self):
    """双周专家项目推送 — 扫描14天未完成项目"""
    try:
        with get_sync_session() as db:
            logger.info("[expert_program_14d_push] scanning")
            # Phase 1: 返回空结果 (后续接入 program_service)
            return {"status": "ok", "processed": 0}
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.governance_tasks.promotion_ceremony", bind=True, max_retries=3, default_retry_delay=30)
def promotion_ceremony(self, user_id: int, from_role: str, to_role: str):
    """事件驱动晋级仪式 — API 调用 promotion_ceremony.delay(user_id, from_role, to_role)"""
    try:
        with get_sync_session() as db:
            logger.info("[promotion_ceremony] user=%d %s→%s", user_id, from_role, to_role)
            # Phase 1: 记录日志 (后续接入 notification_service + 仪式页面触发)
            return {"status": "ok", "user_id": user_id}
    except Exception as e: raise self.retry(exc=e)
