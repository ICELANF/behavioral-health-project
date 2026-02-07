# -*- coding: utf-8 -*-
"""
设备预警 API
Device Alert API

端点:
- GET  /api/v1/alerts/my          — 用户查看自己的预警
- GET  /api/v1/alerts/coach       — 教练查看学员预警
- POST /api/v1/alerts/{id}/read   — 标记已读
- POST /api/v1/alerts/{id}/resolve — 教练标记已处理
"""
import os
import sys
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from core.models import DeviceAlert, User
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/alerts", tags=["设备预警"])


@router.get("/my")
async def get_my_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None, description="warning / danger"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户查看自己的预警（分页）"""
    query = db.query(DeviceAlert).filter(
        DeviceAlert.user_id == current_user.id,
    )
    if severity:
        query = query.filter(DeviceAlert.severity == severity)

    total = query.count()
    alerts = (
        query.order_by(desc(DeviceAlert.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "alerts": [_alert_to_dict(a) for a in alerts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/coach")
async def get_coach_alerts(
    unread_only: bool = Query(False, description="仅未读"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练查看学员预警（分页）"""
    query = db.query(DeviceAlert).filter(
        DeviceAlert.coach_id == current_user.id,
    )
    if unread_only:
        query = query.filter(DeviceAlert.coach_read == False)

    total = query.count()
    alerts = (
        query.order_by(desc(DeviceAlert.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Enrich with student name
    result = []
    for a in alerts:
        d = _alert_to_dict(a)
        student = db.query(User).filter(User.id == a.user_id).first()
        d["student_name"] = student.full_name or student.username if student else "未知"
        result.append(d)

    return {
        "alerts": result,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记预警已读（区分 user_read / coach_read）"""
    alert = db.query(DeviceAlert).filter(DeviceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    # Determine role
    if alert.user_id == current_user.id:
        alert.user_read = True
    elif alert.coach_id == current_user.id:
        alert.coach_read = True
    else:
        raise HTTPException(status_code=403, detail="无权操作此预警")

    db.commit()
    return {"success": True, "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练标记预警已处理"""
    alert = db.query(DeviceAlert).filter(DeviceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")
    if alert.coach_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="无权处理此预警")

    alert.resolved = True
    alert.coach_read = True
    db.commit()
    return {"success": True, "alert_id": alert_id, "message": "预警已处理"}


def _alert_to_dict(alert: DeviceAlert) -> dict:
    """Convert DeviceAlert to dict"""
    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "coach_id": alert.coach_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "data_value": alert.data_value,
        "threshold_value": alert.threshold_value,
        "data_type": alert.data_type,
        "user_read": alert.user_read,
        "coach_read": alert.coach_read,
        "resolved": alert.resolved,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }
