# 行健平台 · 行诊智伴集成代码包
# XZB (行诊智伴 / XingZhen BanShou) Integration
# V1.0 · 2026-02-24

"""
目录结构：
xzb/
├── migrations/
│   └── migration_053_056.sql      # 数据库迁移 (Migrations 053-056)
├── models/
│   ├── xzb_models.py              # SQLAlchemy ORM + Pydantic 模型
│   └── cache_manager.py           # Redis 缓存策略 (§5.2)
├── knowledge/
│   ├── retriever.py               # XZBKnowledgeRetriever (§3.3)
│   └── agent_proxy.py             # XZBAgentProxy (§2.2)
├── rx/
│   └── rx_bridge.py               # XZBRxBridge 处方桥接 (§4.1)
├── style/
│   └── style_adapter.py           # XZBStyleAdapter 风格转换 (§6.1)
├── api/
│   └── xzb_api.py                 # FastAPI 路由 (§7.1-7.4)
├── scheduler/
│   └── jobs.py                    # Celery 定时任务 Job 26-30 (§5.3)
├── ws/
│   └── xzb_events.py              # WebSocket 事件扩展 (§5.4)
└── __init__.py

集成方式：
1. 执行 SQL Migration 053→056
2. 在 FastAPI app 注册路由：app.include_router(xzb_router)
3. 在 Celery beat 添加 XZB_BEAT_SCHEDULE
4. 在 AgentRouter.route() 添加 XZBAgentProxy 检测逻辑
5. 在 WS endpoint 注册 XZBWSHandler

依赖：
- pgvector>=0.3
- fastapi, sqlalchemy[asyncio]
- celery, redis
- pydantic>=2.0
"""

from xzb.models.xzb_models import (
    XZBExpertProfile, XZBConfig, XZBKnowledge,
    XZBKnowledgeRule, XZBConversation, XZBRxFragment,
    XZBExpertIntervention,
    KnowledgeType, EvidenceTier, ActionType, RxStatus,
)
from xzb.knowledge.retriever import XZBKnowledgeRetriever
from xzb.knowledge.agent_proxy import XZBAgentProxy
from xzb.rx.rx_bridge import XZBRxBridge, XZBTriggerDetector
from xzb.style.style_adapter import XZBStyleAdapter, StyleCalibrator
from xzb.models.cache_manager import XZBCacheManager
from xzb.ws.xzb_events import XZBWSEventSender, XZBWSHandler, XZBEventType
from xzb.scheduler.jobs import XZB_BEAT_SCHEDULE
from xzb.api.xzb_api import router as xzb_router

__all__ = [
    # Models
    "XZBExpertProfile", "XZBConfig", "XZBKnowledge",
    "XZBKnowledgeRule", "XZBConversation", "XZBRxFragment",
    "XZBExpertIntervention",
    "KnowledgeType", "EvidenceTier", "ActionType", "RxStatus",
    # Core
    "XZBKnowledgeRetriever", "XZBAgentProxy",
    "XZBRxBridge", "XZBTriggerDetector",
    "XZBStyleAdapter", "StyleCalibrator",
    "XZBCacheManager",
    # WS
    "XZBWSEventSender", "XZBWSHandler", "XZBEventType",
    # Config
    "XZB_BEAT_SCHEDULE",
    # Router
    "xzb_router",
]
