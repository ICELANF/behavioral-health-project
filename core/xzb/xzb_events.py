"""
行智诊疗 WebSocket 事件扩展
在现有 WS /ws/user/{id} 频道上追加5个新事件, 不新建频道
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import UUID

logger = logging.getLogger(__name__)


class XZBEventType:
    EXPERT_MESSAGE    = "xzb_expert_message"
    EXPERT_ONLINE     = "xzb_expert_online"
    KNOWLEDGE_UPDATED = "xzb_knowledge_updated"
    RX_PENDING_REVIEW = "xzb_rx_pending_review"
    KNOWLEDGE_CONFIRM = "xzb_knowledge_confirm"


@dataclass
class XZBExpertMessageEvent:
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
class XZBRxPendingReviewEvent:
    event: str = XZBEventType.RX_PENDING_REVIEW
    fragment_id: str = ""
    expert_id: str = ""
    expert_name: str = ""
    seeker_id: str = ""
    domain: Optional[str] = None
    evidence_tier: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class XZBKnowledgeConfirmEvent:
    event: str = XZBEventType.KNOWLEDGE_CONFIRM
    pending_count: int = 0
    knowledge_previews: list = None
    timestamp: str = ""

    def __post_init__(self):
        if self.knowledge_previews is None:
            self.knowledge_previews = []
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class XZBWSEventSender:
    """行智诊疗 WS 事件发送器 — 包装平台现有 ws_manager"""

    def __init__(self, ws_manager=None):
        self.ws = ws_manager

    def send_expert_message(self, seeker_id: int, expert_id: UUID,
                            expert_name: str, content: str, conversation_id=None):
        event = XZBExpertMessageEvent(
            expert_id=str(expert_id), expert_name=expert_name,
            content=content,
            conversation_id=str(conversation_id) if conversation_id else None,
        )
        self._send(seeker_id, event)

    def notify_coach_rx_pending(self, coach_id: int, fragment_id: UUID,
                                expert_id: UUID, expert_name: str,
                                seeker_id: int, domain=None, evidence_tier=None):
        event = XZBRxPendingReviewEvent(
            fragment_id=str(fragment_id), expert_id=str(expert_id),
            expert_name=expert_name, seeker_id=str(seeker_id),
            domain=domain, evidence_tier=evidence_tier,
        )
        self._send(coach_id, event)

    def notify_expert_knowledge_confirm(self, expert_id: UUID,
                                        pending_count: int, previews: list):
        event = XZBKnowledgeConfirmEvent(
            pending_count=pending_count, knowledge_previews=previews[:3],
        )
        self._send(expert_id, event)

    def _send(self, user_id: Union[int, UUID], event_obj) -> bool:
        if not self.ws:
            logger.debug("XZB WS: no ws_manager, skipping event %s", type(event_obj).__name__)
            return False
        try:
            payload = json.dumps(asdict(event_obj), ensure_ascii=False)
            self.ws.send_personal_message(str(user_id), payload)
            return True
        except Exception as e:
            logger.error("XZB WS send failed user=%s: %s", user_id, e)
            return False
