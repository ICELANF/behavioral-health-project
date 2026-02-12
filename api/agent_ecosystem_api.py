"""
Phase 5: Agent 生态 API

端点:
  GET    /v1/agent-ecosystem/marketplace              — 浏览市场
  POST   /v1/agent-ecosystem/marketplace/publish       — 发布模板到市场
  GET    /v1/agent-ecosystem/marketplace/pending        — 待审核 (admin)
  POST   /v1/agent-ecosystem/marketplace/{id}/approve   — 审核通过
  POST   /v1/agent-ecosystem/marketplace/{id}/reject    — 审核拒绝
  POST   /v1/agent-ecosystem/marketplace/{id}/install   — 安装模板
  GET    /v1/agent-ecosystem/compositions               — 组合列表
  POST   /v1/agent-ecosystem/compositions               — 创建组合
  GET    /v1/agent-ecosystem/compositions/{id}           — 组合详情
  GET    /v1/agent-ecosystem/growth-points               — 我的成长积分
  GET    /v1/agent-ecosystem/growth-points/config        — 积分事件配置
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User
from api.dependencies import get_current_user, require_coach_or_admin, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-ecosystem", tags=["agent-ecosystem"])


# ── Pydantic Schemas ──

class PublishRequest(BaseModel):
    template_id: int
    title: str = Field(..., max_length=128)
    description: str = ""
    category: str = ""
    tags: List[str] = []

class ReviewRequest(BaseModel):
    comment: str = ""

class InstallRequest(BaseModel):
    target_tenant_id: str

class CompositionCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = ""
    pipeline: list = Field(..., description="编排定义")
    merge_strategy: str = "weighted_average"
    tenant_id: Optional[str] = None


# ── Marketplace ──

@router.get("/marketplace")
def browse_marketplace(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """浏览 Agent 模板市场"""
    from core.ecosystem_service import browse_marketplace as _browse

    result = _browse(db, category=category, search=search, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "items": [_listing_to_dict(l) for l in result["items"]],
            "total": result["total"],
        },
    }


@router.post("/marketplace/publish")
def publish_template(
    data: PublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布 Agent 模板到市场"""
    from core.ecosystem_service import publish_to_marketplace
    from core.models import ExpertTenant

    tenant = db.query(ExpertTenant).filter(
        ExpertTenant.expert_user_id == current_user.id,
    ).first()
    if not tenant and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅专家可发布模板")

    tenant_id = tenant.id if tenant else "platform"

    try:
        listing = publish_to_marketplace(
            db=db,
            template_id=data.template_id,
            publisher_id=current_user.id,
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            category=data.category,
            tags=data.tags,
        )
        db.commit()
        return {"success": True, "data": _listing_to_dict(listing)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/marketplace/pending")
def pending_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """待审核市场发布"""
    from core.ecosystem_service import list_pending_listings

    result = list_pending_listings(db, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "items": [_listing_to_dict(l) for l in result["items"]],
            "total": result["total"],
        },
    }


@router.post("/marketplace/{listing_id}/approve")
def approve_listing(
    listing_id: int,
    data: ReviewRequest = ReviewRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """审核通过市场发布"""
    from core.ecosystem_service import approve_listing as _approve

    try:
        listing = _approve(db, listing_id, current_user.id, data.comment)
        db.commit()
        return {"success": True, "data": _listing_to_dict(listing)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/marketplace/{listing_id}/reject")
def reject_listing(
    listing_id: int,
    data: ReviewRequest = ReviewRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """审核拒绝市场发布"""
    from core.ecosystem_service import reject_listing as _reject

    try:
        listing = _reject(db, listing_id, current_user.id, data.comment)
        db.commit()
        return {"success": True, "data": _listing_to_dict(listing)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/marketplace/{listing_id}/install")
def install_template(
    listing_id: int,
    data: InstallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """安装市场模板"""
    from core.ecosystem_service import install_template as _install

    try:
        new_tpl = _install(db, listing_id, current_user.id, data.target_tenant_id)
        db.commit()
        return {
            "success": True,
            "data": {
                "agent_id": new_tpl.agent_id,
                "display_name": new_tpl.display_name,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Composition ──

@router.get("/compositions")
def list_compositions(
    tenant_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出 Agent 组合"""
    from core.ecosystem_service import list_compositions as _list

    result = _list(db, tenant_id=tenant_id, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "items": [_composition_to_dict(c) for c in result["items"]],
            "total": result["total"],
        },
    }


@router.post("/compositions")
def create_composition(
    data: CompositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """创建 Agent 组合"""
    from core.ecosystem_service import create_composition as _create

    try:
        comp = _create(
            db=db,
            name=data.name,
            pipeline=data.pipeline,
            created_by=current_user.id,
            description=data.description,
            tenant_id=data.tenant_id,
            merge_strategy=data.merge_strategy,
        )
        db.commit()
        return {"success": True, "data": _composition_to_dict(comp)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/compositions/{composition_id}")
def get_composition(
    composition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """组合详情"""
    from core.ecosystem_service import get_composition as _get

    comp = _get(db, composition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="组合不存在")
    return {"success": True, "data": _composition_to_dict(comp)}


# ── Growth Points ──

@router.get("/growth-points")
def my_growth_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """我的 Agent 成长积分"""
    from core.ecosystem_service import get_user_growth_points

    data = get_user_growth_points(db, current_user.id)
    return {"success": True, "data": data}


@router.get("/growth-points/config")
def growth_points_config(
    current_user: User = Depends(get_current_user),
):
    """积分事件配置"""
    from core.ecosystem_service import GROWTH_POINT_EVENTS

    return {
        "success": True,
        "data": [
            {"event_type": k, "points": v}
            for k, v in GROWTH_POINT_EVENTS.items()
        ],
    }


# ── 辅助 ──

def _listing_to_dict(listing) -> dict:
    return {
        "id": listing.id,
        "template_id": listing.template_id,
        "publisher_id": listing.publisher_id,
        "tenant_id": listing.tenant_id,
        "title": listing.title,
        "description": listing.description,
        "category": listing.category,
        "tags": listing.tags,
        "status": listing.status,
        "install_count": listing.install_count,
        "avg_rating": listing.avg_rating,
        "rating_count": listing.rating_count,
        "version": listing.version,
        "review_comment": listing.review_comment,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
    }


def _composition_to_dict(comp) -> dict:
    return {
        "id": comp.id,
        "name": comp.name,
        "description": comp.description,
        "tenant_id": comp.tenant_id,
        "pipeline": comp.pipeline,
        "merge_strategy": comp.merge_strategy,
        "is_enabled": comp.is_enabled,
        "is_default": comp.is_default,
        "created_at": comp.created_at.isoformat() if comp.created_at else None,
    }
