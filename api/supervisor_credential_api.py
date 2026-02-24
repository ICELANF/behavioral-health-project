# -*- coding: utf-8 -*-
"""
supervisor_credential_api.py — 督导资质管理API (I-07)

4 个端点:
- POST /api/v1/credentials/grant       — 授予资质 (admin)
- POST /api/v1/credentials/{id}/review  — 年审续期 (admin)
- POST /api/v1/credentials/{id}/revoke  — 吊销资质 (admin)
- GET  /api/v1/credentials/user/{uid}   — 查询用户资质 (admin)
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User
from api.dependencies import require_admin
from core.supervisor_credential_service import SupervisorCredentialService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])

_svc = SupervisorCredentialService()


class GrantRequest(BaseModel):
    user_id: int
    credential_type: str = Field(..., description="physician_license / coach_certification / phd_supervision")
    credential_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issued_at: Optional[datetime] = None


class ReviewRequest(BaseModel):
    notes: Optional[str] = None


class RevokeRequest(BaseModel):
    reason: str = ""


@router.post("/grant")
def grant_credential(
    req: GrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """授予资质 + 触发角色升级"""
    try:
        result = _svc.grant_credential(
            db=db,
            user_id=req.user_id,
            credential_type=req.credential_type,
            granted_by=current_user.id,
            credential_number=req.credential_number,
            issuing_authority=req.issuing_authority,
            issued_at=req.issued_at,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{credential_id}/review")
def review_credential(
    credential_id: int,
    req: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """年审续期"""
    try:
        result = _svc.review_credential(
            db=db,
            credential_id=credential_id,
            reviewer_id=current_user.id,
            notes=req.notes,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{credential_id}/revoke")
def revoke_credential(
    credential_id: int,
    req: RevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """吊销资质"""
    try:
        result = _svc.revoke_credential(
            db=db,
            credential_id=credential_id,
            revoked_by=current_user.id,
            reason=req.reason,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
def get_user_credentials(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """查询用户所有资质"""
    data = _svc.get_user_credentials(db, user_id)
    return {"success": True, "data": data, "total": len(data)}
