"""
V4.0 Unified Intervention Narrative — 四种干预统一叙事 (MEU-36)

Unify 4 intervention types into coherent user narrative:
  1. Device push (设备推送)
  2. Micro-action (微行动)
  3. Agent dialog (AI对话)
  4. Coach message (教练消息)

Timeline view combining all touchpoints with stage context.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from core.models import (
    User, JourneyState,
    ChatSession, ChatMessage,
    MicroActionTask,
)

logger = logging.getLogger(__name__)


class UnifiedNarrativeService:
    """统一干预叙事服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_timeline(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 50,
    ) -> dict:
        """获取用户统一干预时间线"""
        since = datetime.utcnow() - timedelta(days=days)

        events = []

        # 1. Micro-actions
        try:
            actions = self.db.query(MicroActionTask).filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.created_at >= since,
            ).order_by(desc(MicroActionTask.created_at)).limit(limit).all()

            for a in actions:
                events.append({
                    "type": "micro_action",
                    "id": a.id,
                    "title": a.title,
                    "domain": a.domain,
                    "status": a.status,
                    "timestamp": str(a.created_at) if a.created_at else None,
                    "icon": "check-circle" if a.status == "completed" else "clock",
                })
        except Exception as e:
            logger.warning(f"Micro-action query failed: {e}")

        # 2. Agent dialogs (chat sessions)
        try:
            sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= since,
            ).order_by(desc(ChatSession.created_at)).limit(20).all()

            for s in sessions:
                events.append({
                    "type": "agent_dialog",
                    "id": s.id,
                    "title": s.title or "AI对话",
                    "message_count": s.message_count,
                    "timestamp": str(s.created_at) if s.created_at else None,
                    "icon": "message",
                })
        except Exception as e:
            logger.warning(f"Chat session query failed: {e}")

        # 3. Device alerts (if available)
        try:
            from core.models import DeviceAlert
            alerts = self.db.query(DeviceAlert).filter(
                DeviceAlert.user_id == user_id,
                DeviceAlert.created_at >= since,
            ).order_by(desc(DeviceAlert.created_at)).limit(10).all()

            for al in alerts:
                events.append({
                    "type": "device_alert",
                    "id": al.id,
                    "title": al.alert_type if hasattr(al, 'alert_type') else "设备预警",
                    "severity": al.severity if hasattr(al, 'severity') else "info",
                    "timestamp": str(al.created_at) if al.created_at else None,
                    "icon": "alert",
                })
        except Exception:
            pass  # DeviceAlert may not exist

        # 4. Coach messages (if available)
        try:
            from core.models import CoachMessage
            messages = self.db.query(CoachMessage).filter(
                CoachMessage.recipient_id == user_id,
                CoachMessage.created_at >= since,
            ).order_by(desc(CoachMessage.created_at)).limit(10).all()

            for m in messages:
                events.append({
                    "type": "coach_message",
                    "id": m.id,
                    "title": "教练消息",
                    "sender_id": m.sender_id,
                    "timestamp": str(m.created_at) if m.created_at else None,
                    "icon": "user",
                })
        except Exception:
            pass  # CoachMessage may not exist

        # Sort by timestamp
        events.sort(
            key=lambda e: e.get("timestamp", ""),
            reverse=True,
        )

        # Get journey context
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()

        return {
            "user_id": user_id,
            "days": days,
            "journey_stage": journey.journey_stage if journey else "s0_authorization",
            "agency_mode": journey.agency_mode if journey else "passive",
            "total_events": len(events),
            "events": events[:limit],
            "summary": {
                "micro_actions": sum(1 for e in events if e["type"] == "micro_action"),
                "agent_dialogs": sum(1 for e in events if e["type"] == "agent_dialog"),
                "device_alerts": sum(1 for e in events if e["type"] == "device_alert"),
                "coach_messages": sum(1 for e in events if e["type"] == "coach_message"),
            },
        }

    def get_narrative_summary(self, user_id: int, days: int = 7) -> dict:
        """生成用户成长叙事摘要"""
        timeline = self.get_user_timeline(user_id, days)

        completed_actions = sum(
            1 for e in timeline["events"]
            if e["type"] == "micro_action" and e.get("status") == "completed"
        )
        total_actions = sum(
            1 for e in timeline["events"]
            if e["type"] == "micro_action"
        )
        dialog_count = timeline["summary"]["agent_dialogs"]

        # Build narrative based on agency_mode
        agency_mode = timeline.get("agency_mode", "passive")
        stage = timeline.get("journey_stage", "s0_authorization")

        if agency_mode == "passive":
            narrative_style = "这周的健康旅程中..."
        elif agency_mode == "transitional":
            narrative_style = "你这周的探索中..."
        else:
            narrative_style = "你这周..."

        narrative_parts = [narrative_style]
        if total_actions > 0:
            rate = completed_actions / total_actions if total_actions else 0
            narrative_parts.append(
                f"完成了{completed_actions}/{total_actions}个微行动({rate:.0%})"
            )
        if dialog_count > 0:
            narrative_parts.append(f"进行了{dialog_count}次AI对话")

        return {
            "user_id": user_id,
            "days": days,
            "stage": stage,
            "agency_mode": agency_mode,
            "narrative": "，".join(narrative_parts) + "。",
            "stats": timeline["summary"],
            "completion_rate": completed_actions / total_actions if total_actions else 0,
        }
