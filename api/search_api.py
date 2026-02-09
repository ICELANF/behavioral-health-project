# -*- coding: utf-8 -*-
"""
全平台搜索 API
Global Search API

提供跨模型关键词搜索，支持用户、挑战、微行动、预警、消息五类检索。
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import (
    User, ChallengeTemplate, MicroActionTask, DeviceAlert, CoachMessage
)
from api.dependencies import require_coach_or_admin

router = APIRouter(tags=["search"])


def _do_search(q: str, limit: int, db: Session) -> dict:
    """搜索核心逻辑"""
    per_category = min(limit, 5)
    keyword = f"%{q}%"
    results: Dict[str, List[Dict[str, Any]]] = {}

    # --- users ---
    users = (
        db.query(User)
        .filter(
            (User.username.ilike(keyword)) | (User.full_name.ilike(keyword)) | (User.email.ilike(keyword))
        )
        .limit(per_category)
        .all()
    )
    results["users"] = [
        {"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role.value}
        for u in users
    ]

    # --- challenges ---
    challenges = (
        db.query(ChallengeTemplate)
        .filter(
            (ChallengeTemplate.title.ilike(keyword)) | (ChallengeTemplate.description.ilike(keyword))
        )
        .limit(per_category)
        .all()
    )
    results["challenges"] = [
        {"id": c.id, "title": c.title, "status": c.status.value if c.status else None, "category": c.category}
        for c in challenges
    ]

    # --- micro_actions ---
    actions = (
        db.query(MicroActionTask)
        .filter(
            (MicroActionTask.title.ilike(keyword)) | (MicroActionTask.description.ilike(keyword))
        )
        .limit(per_category)
        .all()
    )
    results["micro_actions"] = [
        {"id": a.id, "title": a.title, "domain": a.domain, "status": a.status}
        for a in actions
    ]

    # --- alerts ---
    alerts = (
        db.query(DeviceAlert)
        .filter(
            (DeviceAlert.message.ilike(keyword)) | (DeviceAlert.alert_type.ilike(keyword))
        )
        .limit(per_category)
        .all()
    )
    results["alerts"] = [
        {"id": a.id, "alert_type": a.alert_type, "message": a.message, "severity": a.severity}
        for a in alerts
    ]

    # --- messages ---
    messages = (
        db.query(CoachMessage)
        .filter(CoachMessage.content.ilike(keyword))
        .limit(per_category)
        .all()
    )
    results["messages"] = [
        {
            "id": m.id,
            "content": m.content[:80] if m.content else "",
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]

    total = sum(len(v) for v in results.values())
    return {"query": q, "results": results, "total": total}


@router.get("/api/v1/search")
def global_search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    current_user=Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """全平台搜索（标准路径）"""
    return _do_search(q, limit, db)


