"""
Event Tracking API — batch event ingestion for H5 analytics.
Writes to existing user_activity_logs table.

POST /api/v1/events/track — batch event ingestion
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_async_db
from core.models import User

router = APIRouter(prefix="/api/v1/events", tags=["Event Tracking"])


# ── Schemas ──

class EventItem(BaseModel):
    event_type: str  # page_view, button_click, task_complete, feature_use, session_start, session_end, food_scan, chat_message
    properties: Optional[dict] = None
    client_timestamp: Optional[str] = None


class TrackRequest(BaseModel):
    events: List[EventItem]


# Map frontend event types → activity_type in user_activity_logs
_EVENT_MAP = {
    "page_view": "page_view",
    "button_click": "interact",
    "task_complete": "task",
    "feature_use": "feature",
    "session_start": "login",
    "session_end": "logout",
    "food_scan": "food_scan",
    "chat_message": "chat",
    "login": "login",
    "share": "share",
    "learn": "learn",
    "comment": "comment",
    "like": "like",
    "exam": "exam",
    "assess": "assess",
}


@router.post("/track")
async def track_events(
    req: TrackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Batch event ingestion — max 100 events per request."""
    if len(req.events) > 100:
        raise HTTPException(400, "Max 100 events per batch")

    inserted = 0
    for evt in req.events:
        activity_type = _EVENT_MAP.get(evt.event_type, evt.event_type[:30])
        detail = evt.properties or {}
        if evt.client_timestamp:
            detail["client_ts"] = evt.client_timestamp
        detail["raw_event"] = evt.event_type

        try:
            await db.execute(
                text("""
                    INSERT INTO user_activity_logs (user_id, activity_type, detail, created_at)
                    VALUES (:uid, :atype, CAST(:detail AS json), NOW())
                """),
                {
                    "uid": current_user.id,
                    "atype": activity_type,
                    "detail": __import__("json").dumps(detail, ensure_ascii=False),
                },
            )
            inserted += 1
        except Exception as e:
            logger.warning(f"Event insert failed: {e}")

    if inserted:
        await db.commit()

    return {"success": True, "tracked": inserted}
