"""EventType → Celery 桥接。trigger_router 路由不变，执行方式从同步变异步。"""
import logging, importlib
from api.worker import celery_app
from api.tasks.db import get_sync_session
logger = logging.getLogger(__name__)

@celery_app.task(name="api.tasks.event_tasks.process_event", bind=True, max_retries=3, default_retry_delay=10)
def process_event(self, event_type: str, handler_name: str, data: dict):
    try:
        mod = importlib.import_module("core.v14.trigger_router")
        handler = getattr(mod, handler_name, None)
        if not handler: return {"status":"error","reason":f"{handler_name} not found"}
        with get_sync_session() as db:
            try: handler(data, db=db)
            except TypeError: handler(data)
        logger.info("[process_event] %s.%s ok", event_type, handler_name)
        return {"status":"ok"}
    except Exception as e:
        logger.exception("[process_event] %s.%s fail", event_type, handler_name)
        raise self.retry(exc=e)

@celery_app.task(name="api.tasks.event_tasks.process_event_batch")
def process_event_batch(events: list):
    for e in events: process_event.delay(e["event_type"], e["handler_name"], e["data"])
    return {"dispatched": len(events)}
