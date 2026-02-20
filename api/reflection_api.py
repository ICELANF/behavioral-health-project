"""
V4.0 Reflection Journal API — 反思日志 (MEU-30)

Endpoints:
  POST /entries              创建反思日志
  GET  /entries              列出反思日志
  GET  /entries/{id}         获取单条日志
  GET  /prompts              获取反思提示
  GET  /stats                反思深度统计
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from loguru import logger

from api.dependencies import get_current_user, get_db
from core.models import User
from core.reflection_service import ReflectionService

router = APIRouter(prefix="/api/v1/reflection", tags=["reflection"])


class CreateReflectionRequest(BaseModel):
    content: str
    title: Optional[str] = None
    journal_type: str = "freeform"
    tags: Optional[List[str]] = None
    prompt_used: Optional[str] = None


@router.post("/entries")
def create_reflection(
    req: CreateReflectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建反思日志"""
    try:
        svc = ReflectionService(db)
        result = svc.create_entry(
            current_user.id,
            req.content,
            title=req.title,
            journal_type=req.journal_type,
            tags=req.tags,
            prompt_used=req.prompt_used,
        )
        db.commit()
    except Exception:
        db.rollback()
        result = {"id": 0, "content": req.content, "title": req.title, "status": "pending"}

    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=current_user.id,
            action="reflection_create",
            point_type="awareness",
            amount=5,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    return result


@router.get("/entries")
def list_reflections(
    journal_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出反思日志"""
    try:
        svc = ReflectionService(db)
        return svc.list_entries(current_user.id, journal_type, limit, offset)
    except Exception:
        return {"items": [], "total": 0}


@router.get("/entries/{entry_id}")
def get_reflection(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条反思日志"""
    svc = ReflectionService(db)
    result = svc.get_entry(entry_id, current_user.id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/prompts")
def get_prompts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取基于当前agency_mode的反思提示"""
    svc = ReflectionService(db)
    return svc.get_prompts(current_user.id)


@router.get("/stats")
def get_reflection_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取反思深度统计"""
    svc = ReflectionService(db)
    return svc.get_depth_stats(current_user.id, days)
