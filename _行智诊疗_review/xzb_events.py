"""
行诊智伴 WebSocket 事件扩展（文档 §5.4）
在现有 WS /ws/user/{id} 频道上追加5个新事件
不新建频道，复用平台现有 WebSocket 基础设施
"""
from __future__ import annotations
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 事件定义（文档 §5.4 5个新增事件）
# ─────────────────────────────────────────────

class XZBEventType:
    EXPERT_MESSAGE    = "xzb_expert_message"     # 专家异步介入/主动消息 → 受益者
    EXPERT_ONLINE     = "xzb_expert_online"      # 专家在线时段激活 → 该专家所有受益者
    KNOWLEDGE_UPDATED = "xzb_knowledge_updated"  # 知识库重要更新 → 订阅该专家的受益者
    RX_PENDING_REVIEW = "xzb_rx_pending_review"  # XZBRxFragment进入审核队列 → 教练
    KNOWLEDGE_CONFIRM = "xzb_knowledge_confirm"  # 对话沉淀识别到新知识 → 专家本人


@dataclass
class XZBExpertMessageEvent:
    """专家异步介入消息"""
    event: str = XZBEventType.EXPERT_MESSAGE
    expert_id: str = ""
    expert_name: str = ""
    content: str = ""
    conversation_id: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class XZBExpertOnlineEvent:
    """专家上线通知"""
    event: str = XZBEventType.EXPERT_ONLINE
    expert_id: str = ""
    expert_name: str = ""
    online_until: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class XZBKnowledgeUpdatedEvent:
    """知识库更新通知"""
    event: str = XZBEventType.KNOWLEDGE_UPDATED
    expert_id: str = ""
    update_summary: str = ""
    knowledge_count: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class XZBRxPendingReviewEvent:
    """处方草案进入审核队列通知 → 教练"""
    event: str = XZBEventType.RX_PENDING_REVIEW
    fragment_id: str = ""
    expert_id: str = ""
    expert_name: str = ""
    seeker_id: str = ""
    seeker_name: str = ""
    domain: Optional[str] = None
    evidence_tier: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class XZBKnowledgeConfirmEvent:
    """对话沉淀新知识待确认通知 → 专家"""
    event: str = XZBEventType.KNOWLEDGE_CONFIRM
    pending_count: int = 0
    knowledge_previews: list = None
    conversation_id: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if self.knowledge_previews is None:
            self.knowledge_previews = []
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


# ─────────────────────────────────────────────
# WebSocket 事件发送器
# 复用平台现有 WS Manager（/ws/user/{id} 频道）
# ─────────────────────────────────────────────

class XZBWSEventSender:
    """
    行诊智伴 WebSocket 事件发送器
    包装平台现有 ws_manager，追加 XZB 事件
    """

    def __init__(self, ws_manager):
        self.ws = ws_manager   # 平台现有 WebSocketManager

    async def send_expert_message(
        self,
        seeker_id: UUID,
        expert_id: UUID,
        expert_name: str,
        content: str,
        conversation_id: Optional[UUID] = None,
    ):
        """xzb_expert_message → 受益者"""
        event = XZBExpertMessageEvent(
            expert_id=str(expert_id),
            expert_name=expert_name,
            content=content,
            conversation_id=str(conversation_id) if conversation_id else None,
        )
        await self._send(seeker_id, event)
        logger.info("WS xzb_expert_message → seeker %s from expert %s", seeker_id, expert_id)

    async def broadcast_expert_online(
        self,
        expert_id: UUID,
        expert_name: str,
        seeker_ids: list,
        online_until: Optional[datetime] = None,
    ):
        """xzb_expert_online → 该专家所有受益者"""
        event = XZBExpertOnlineEvent(
            expert_id=str(expert_id),
            expert_name=expert_name,
            online_until=online_until.isoformat() if online_until else None,
        )
        for seeker_id in seeker_ids:
            await self._send(seeker_id, event)
        logger.info(
            "WS xzb_expert_online broadcast to %d seekers for expert %s",
            len(seeker_ids), expert_id
        )

    async def notify_knowledge_updated(
        self,
        expert_id: UUID,
        subscriber_ids: list,
        update_summary: str,
        knowledge_count: int = 0,
    ):
        """xzb_knowledge_updated → 订阅该专家的受益者"""
        event = XZBKnowledgeUpdatedEvent(
            expert_id=str(expert_id),
            update_summary=update_summary,
            knowledge_count=knowledge_count,
        )
        for subscriber_id in subscriber_ids:
            await self._send(subscriber_id, event)

    async def notify_coach_rx_pending(
        self,
        coach_id: UUID,
        fragment_id: UUID,
        expert_id: UUID,
        expert_name: str,
        seeker_id: UUID,
        seeker_name: str,
        domain: Optional[str] = None,
        evidence_tier: Optional[str] = None,
    ):
        """xzb_rx_pending_review → 负责该受益者的教练（铁律执行层）"""
        event = XZBRxPendingReviewEvent(
            fragment_id=str(fragment_id),
            expert_id=str(expert_id),
            expert_name=expert_name,
            seeker_id=str(seeker_id),
            seeker_name=seeker_name,
            domain=domain,
            evidence_tier=evidence_tier,
        )
        await self._send(coach_id, event)
        logger.info(
            "WS xzb_rx_pending_review → coach %s fragment %s", coach_id, fragment_id
        )

    async def notify_expert_knowledge_confirm(
        self,
        expert_id: UUID,
        pending_count: int,
        knowledge_previews: list,
        conversation_id: Optional[UUID] = None,
    ):
        """xzb_knowledge_confirm → 专家本人（专家工作台频道）"""
        event = XZBKnowledgeConfirmEvent(
            pending_count=pending_count,
            knowledge_previews=knowledge_previews[:3],  # 最多显示3条预览
            conversation_id=str(conversation_id) if conversation_id else None,
        )
        await self._send(expert_id, event)
        logger.info(
            "WS xzb_knowledge_confirm → expert %s pending=%d", expert_id, pending_count
        )

    async def _send(self, user_id: UUID, event_obj) -> bool:
        """
        通过平台现有 ws_manager 发送事件
        格式与平台现有 prescription_approved 等事件保持一致
        """
        try:
            payload = json.dumps(asdict(event_obj), ensure_ascii=False)
            await self.ws.send_personal_message(str(user_id), payload)
            return True
        except Exception as e:
            logger.error("WS send failed user=%s event=%s: %s", user_id, type(event_obj).__name__, e)
            return False


# ─────────────────────────────────────────────
# 事件处理器注册（集成到平台现有 WS 路由）
# ─────────────────────────────────────────────

class XZBWSHandler:
    """
    处理来自客户端的 XZB 相关 WS 消息
    注册到平台现有 WS 消息路由器
    """

    async def handle(self, user_id: str, message: Dict[str, Any], db) -> Optional[Dict]:
        event_type = message.get("type", "")

        handlers = {
            "xzb:expert:set_online":    self._handle_set_online,
            "xzb:expert:intervene":     self._handle_intervene,
            "xzb:knowledge:confirm":    self._handle_knowledge_confirm,
        }

        handler = handlers.get(event_type)
        if not handler:
            return None

        return await handler(user_id, message, db)

    async def _handle_set_online(self, user_id: str, message: dict, db) -> Dict:
        """专家设置在线状态"""
        from xzb.models.xzb_models import XZBExpertProfile
        from sqlalchemy import select
        result = await db.execute(
            select(XZBExpertProfile).where(XZBExpertProfile.user_id == user_id)
        )
        expert = result.scalar_one_or_none()
        if not expert:
            return {"error": "not_expert"}

        # 写入 Redis 在线状态
        # await redis.setex(f"xzb:expert:{expert.id}:online", 300, "1")
        expert.last_active_at = datetime.utcnow()
        await db.commit()

        return {"type": "xzb:expert:online_ack", "status": "online"}

    async def _handle_intervene(self, user_id: str, message: dict, db) -> Dict:
        """专家实时介入对话"""
        conversation_id = message.get("conversation_id")
        content = message.get("content", "")
        return {"type": "xzb:expert:intervene_ack", "conversation_id": conversation_id}

    async def _handle_knowledge_confirm(self, user_id: str, message: dict, db) -> Dict:
        """专家确认对话沉淀知识"""
        knowledge_id = message.get("knowledge_id")
        action = message.get("action", "confirm")
        return {"type": "xzb:knowledge:confirm_ack", "knowledge_id": knowledge_id, "action": action}


# ─────────────────────────────────────────────
# 集成说明（伪代码，对接平台现有 WS）
# ─────────────────────────────────────────────
"""
# 在平台现有 websocket_endpoint 中注册 XZB 处理器：

from xzb.ws.xzb_events import XZBWSHandler, XZBWSEventSender

xzb_ws_handler = XZBWSHandler()
xzb_ws_sender = XZBWSEventSender(ws_manager)

@app.websocket("/ws/user/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # 优先尝试 XZB 事件处理
            xzb_response = await xzb_ws_handler.handle(user_id, data, db)
            if xzb_response:
                await websocket.send_json(xzb_response)
                continue
            
            # 其他事件由平台现有处理器处理
            await existing_ws_handler.handle(user_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
"""
