"""
V4.0 Peer Support API — 同伴支持 + L2.5实习教练

MEU-26: Sharer Peer Support + L2.5 Intern Coach

Endpoints:
  GET  /status                   同伴支持状态
  GET  /intern-coach/eligibility 实习教练资格检查
  POST /intern-coach/apply       申请实习教练
  GET  /intern-coaches           实习教练列表 (admin)
  GET  /metrics                  同伴支持指标 (admin)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, require_admin
from core.models import User
from core.peer_support_service import PeerSupportService

router = APIRouter(prefix="/api/v1/peer-support", tags=["peer-support"])


@router.get("/status")
def peer_support_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的同伴支持状态"""
    svc = PeerSupportService(db)
    result = svc.get_peer_support_status(current_user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/intern-coach/eligibility")
def check_intern_eligibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """检查实习教练资格"""
    svc = PeerSupportService(db)
    result = svc.check_intern_coach_eligibility(current_user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/intern-coach/apply")
def apply_intern_coach(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """申请成为实习教练"""
    svc = PeerSupportService(db)
    result = svc.apply_intern_coach(current_user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.get("/intern-coaches")
def list_intern_coaches(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """实习教练列表 (管理员)"""
    svc = PeerSupportService(db)
    return {"intern_coaches": svc.get_intern_coaches()}


@router.get("/metrics")
def peer_support_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """全平台同伴支持指标 (管理员)"""
    svc = PeerSupportService(db)
    return svc.get_peer_support_metrics()
