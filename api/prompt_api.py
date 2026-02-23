# -*- coding: utf-8 -*-
"""
Prompt 模板管理 API

端点:
- GET    /api/v1/prompts              — 列表（支持筛选）
- GET    /api/v1/prompts/{id}         — 详情
- POST   /api/v1/prompts              — 新建
- PUT    /api/v1/prompts/{id}         — 更新
- DELETE /api/v1/prompts/{id}         — 删除
"""
import os
import sys
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from core.models import User, PromptTemplate
from api.dependencies import require_coach_or_admin

router = APIRouter(prefix="/api/v1/prompts", tags=["Prompt模板"])


# ── Pydantic schemas ──

class PromptCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., max_length=30)
    content: str
    variables: Optional[List[str]] = []
    ttm_stage: Optional[str] = None
    trigger_domain: Optional[str] = None
    is_active: bool = True


class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=30)
    content: Optional[str] = None
    variables: Optional[List[str]] = None
    ttm_stage: Optional[str] = None
    trigger_domain: Optional[str] = None
    is_active: Optional[bool] = None


def _to_dict(p: PromptTemplate) -> dict:
    return {
        "prompt_id": str(p.id),
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "category": p.category,
        "content": p.content,
        "variables": p.variables or [],
        "ttm_stage": p.ttm_stage,
        "trigger_domain": p.trigger_domain,
        "is_active": p.is_active,
        "created_by": p.created_by,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
async def list_prompts(
    category: Optional[str] = Query(None),
    ttm_stage: Optional[str] = Query(None),
    trigger_domain: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取 Prompt 模板列表"""
    q = db.query(PromptTemplate)
    if category:
        q = q.filter(PromptTemplate.category == category)
    if ttm_stage:
        q = q.filter(PromptTemplate.ttm_stage == ttm_stage)
    if trigger_domain:
        q = q.filter(PromptTemplate.trigger_domain == trigger_domain)
    if is_active is not None:
        q = q.filter(PromptTemplate.is_active == is_active)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            PromptTemplate.name.ilike(like) | PromptTemplate.content.ilike(like)
        )
    total = q.count()
    items = q.order_by(PromptTemplate.updated_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_to_dict(p) for p in items], "total": total}


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取单个 Prompt 模板"""
    p = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="模板不存在")
    return _to_dict(p)


@router.post("")
async def create_prompt(
    body: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """新建 Prompt 模板"""
    p = PromptTemplate(
        name=body.name,
        description=body.description,
        category=body.category,
        content=body.content,
        variables=body.variables or [],
        ttm_stage=body.ttm_stage,
        trigger_domain=body.trigger_domain,
        is_active=body.is_active,
        created_by=current_user.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_dict(p)


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: int,
    body: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新 Prompt 模板"""
    p = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="模板不存在")
    update_data = body.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _to_dict(p)


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """删除 Prompt 模板"""
    p = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(p)
    db.commit()
    return {"message": "已删除", "id": prompt_id}
