"""
supervision_api.py — 督导会议 CRUD API

路由前缀: /api/v1/supervision
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_coach_or_admin, get_db
from core.models import User
from core.supervision_service import (
    SupervisionService, _record_to_dict, VALID_SESSION_TYPES,
)

router = APIRouter(prefix="/api/v1/supervision", tags=["supervision"])

_svc = SupervisionService()


# ── Schemas ──

class CreateSessionRequest(BaseModel):
    coach_id: int
    session_type: str = Field(..., description=f"类型: {VALID_SESSION_TYPES}")
    scheduled_at: Optional[datetime] = None
    template_id: Optional[str] = None
    notes: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    session_notes: Optional[str] = None
    action_items: Optional[list] = None
    quality_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    compliance_met: Optional[bool] = None
    scheduled_at: Optional[datetime] = None


class TransitionRequest(BaseModel):
    target_status: str = Field(..., description="目标状态: in_progress / completed / cancelled")


# ── Endpoints ──

@router.post("/sessions")
def create_supervision_session(
    data: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """创建督导会议"""
    try:
        record = _svc.create_session(
            db=db,
            supervisor=current_user,
            coach_id=data.coach_id,
            session_type=data.session_type,
            scheduled_at=data.scheduled_at,
            template_id=data.template_id,
            notes=data.notes,
        )
        db.commit()
        db.refresh(record)
        return {"success": True, "data": _record_to_dict(record, db)}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
def list_supervision_sessions(
    coach_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """列出督导会议 (督导者看自己创建的, admin 看全部)"""
    supervisor_id = None if current_user.role.value == "admin" else current_user.id
    offset = (page - 1) * page_size
    records, total = _svc.list_sessions(
        db=db,
        supervisor_id=supervisor_id,
        coach_id=coach_id,
        status=status,
        limit=page_size,
        offset=offset,
    )
    return {
        "success": True,
        "data": [_record_to_dict(r, db) for r in records],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/sessions/{session_id}")
def get_supervision_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取单条督导记录"""
    record = _svc.get_session(db, session_id)
    if not record:
        raise HTTPException(status_code=404, detail="督导记录不存在")
    # 权限: 自己创建 / 被督导教练 / admin
    if (
        current_user.role.value != "admin"
        and record.supervisor_id != current_user.id
        and record.coach_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="无权查看此督导记录")
    return {"success": True, "data": _record_to_dict(record, db)}


@router.put("/sessions/{session_id}")
def update_supervision_session(
    session_id: int,
    data: UpdateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新督导记录 (仅督导者/admin)"""
    try:
        record = _svc.update_session(
            db=db,
            record_id=session_id,
            supervisor=current_user,
            session_notes=data.session_notes,
            action_items=data.action_items,
            quality_rating=data.quality_rating,
            compliance_met=data.compliance_met,
            scheduled_at=data.scheduled_at,
        )
        db.commit()
        db.refresh(record)
        return {"success": True, "data": _record_to_dict(record, db)}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/transition")
def transition_session_status(
    session_id: int,
    data: TransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """状态转换 (scheduled→in_progress→completed / cancelled)"""
    try:
        record = _svc.transition_status(
            db=db,
            record_id=session_id,
            supervisor=current_user,
            target_status=data.target_status,
        )
        db.commit()
        db.refresh(record)
        return {"success": True, "data": _record_to_dict(record, db)}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
def supervision_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """督导统计 (当前用户)"""
    stats = _svc.get_stats(db, current_user.id)
    return {"success": True, "data": stats}


@router.post("/sessions/{session_id}/dispatch")
def dispatch_action_items(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """I-03: 督导行动项派发 — 完成会议后分发 action_items"""
    try:
        result = _svc.dispatch_action_items(db, session_id, current_user)
        return {"success": True, "data": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-coaches")
def list_my_coaches(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """列出当前督导专家管理的教练 (通过督导记录去重)"""
    from core.models import CoachSupervisionRecord, User as UserModel
    from sqlalchemy import distinct

    coach_ids = db.query(distinct(CoachSupervisionRecord.coach_id)).filter(
        CoachSupervisionRecord.supervisor_id == current_user.id,
    ).all()
    coach_ids = [cid[0] for cid in coach_ids]

    if not coach_ids:
        return {"success": True, "data": [], "total": 0}

    coaches = db.query(UserModel).filter(UserModel.id.in_(coach_ids)).all()
    data = [
        {
            "id": c.id,
            "username": c.username,
            "full_name": c.full_name,
            "role": c.role.value if c.role else "",
            "is_active": c.is_active,
        }
        for c in coaches
    ]
    return {"success": True, "data": data, "total": len(data)}
