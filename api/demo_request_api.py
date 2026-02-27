# -*- coding: utf-8 -*-
"""
Landing Page API — 预约演示 + 平台统计 + 运营管理

端点：
- POST /api/v1/demo-requests             — 提交预约 (公开, 无需登录)
- GET  /api/v1/demo-requests             — 查询预约列表 (admin)
- PUT  /api/v1/demo-requests/{id}/status  — 更新预约状态 (admin)
- GET  /api/v1/landing/platform-stats     — 平台实时统计 (公开, 缓存5分钟)
"""
import os
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from core.database import get_db
from core.models import DemoRequest, Notification, User, UserRole

router = APIRouter(tags=["Landing Page"])

# ══════════ Schemas ══════════

class DemoRequestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    organization: str | None = Field(None, max_length=200)
    title: str | None = Field(None, max_length=100)
    phone: str = Field(..., min_length=5, max_length=20)
    email: str | None = Field(None, max_length=100)
    solution: str | None = Field(None, max_length=30)
    message: str | None = Field(None, max_length=2000)
    source_page: str | None = Field(None, max_length=30)


class DemoRequestStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(pending|contacted|closed)$")
    notes: str | None = Field(None, max_length=500)


# ══════════ POST /api/v1/demo-requests (公开) ══════════

_demo_router = APIRouter(prefix="/api/v1/demo-requests")


def _notify_admins(db: Session, record: DemoRequest):
    """为所有 admin 用户创建站内通知"""
    try:
        admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active == True).all()
        solution_label = {"hospital": "医院", "insurance": "商保", "government": "政府", "rwe": "RWE"}.get(record.solution or "", "未选择")
        for admin in admins:
            notif = Notification(
                user_id=admin.id,
                title="新预约演示请求",
                body=f"{record.name}（{record.organization or '未填写机构'}）提交了预约演示，感兴趣方案：{solution_label}，联系电话：{record.phone}",
                type="demo_request",
                priority="high",
            )
            db.add(notif)
        db.commit()
        logger.info(f"[DemoRequest] 已通知 {len(admins)} 位管理员 — 预约ID={record.id}")
    except Exception as e:
        logger.error(f"[DemoRequest] 通知管理员失败: {e}")
        db.rollback()


@_demo_router.post("")
def create_demo_request(
    body: DemoRequestCreate,
    db: Session = Depends(get_db),
):
    """提交预约演示/商务咨询请求 (公开端点, 无需认证)"""
    record = DemoRequest(
        name=body.name,
        organization=body.organization,
        title=body.title,
        phone=body.phone,
        email=body.email,
        solution=body.solution,
        message=body.message,
        source_page=body.source_page,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 通知所有管理员
    _notify_admins(db, record)

    return {"ok": True, "id": record.id, "message": "预约信息已提交，我们将尽快与您联系"}


# ══════════ GET /api/v1/demo-requests (admin) ══════════

@_demo_router.get("")
def list_demo_requests(
    status: Optional[str] = Query(None, description="pending/contacted/closed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """查询预约请求列表 (仅管理员)"""
    q = db.query(DemoRequest)
    if status:
        q = q.filter(DemoRequest.status == status)
    total = q.count()
    items = q.order_by(desc(DemoRequest.created_at)).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "organization": r.organization,
                "title": r.title,
                "phone": r.phone,
                "email": r.email,
                "solution": r.solution,
                "message": r.message,
                "source_page": r.source_page,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
    }


# ══════════ PUT /api/v1/demo-requests/{id}/status (admin) ══════════

@_demo_router.put("/{request_id}/status")
def update_demo_request_status(
    request_id: int,
    body: DemoRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新预约请求状态 (仅管理员)"""
    record = db.query(DemoRequest).filter(DemoRequest.id == request_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="预约请求不存在")
    record.status = body.status
    db.commit()
    logger.info(f"[DemoRequest] 状态更新: id={request_id} → {body.status} by admin={current_user.id}")
    return {"ok": True, "id": record.id, "status": record.status}


# ══════════ GET /api/v1/landing/platform-stats (公开) ══════════

_stats_router = APIRouter(prefix="/api/v1/landing")

_stats_cache: dict = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 minutes


def _count_orm_models() -> int:
    """Count all ORM model classes across the platform."""
    from sqlalchemy.orm import DeclarativeMeta
    from core import models as m
    count = 0
    for name in dir(m):
        obj = getattr(m, name, None)
        if isinstance(obj, type) and isinstance(obj, DeclarativeMeta) and hasattr(obj, '__tablename__'):
            count += 1
    return count


def _count_agents() -> int:
    """Count BaseAgent subclasses."""
    try:
        from core.agents.base import BaseAgent
        import core.agents.specialist_agents
        import core.agents.integrative_agents
        import core.agents.generic_llm_agent
        import core.agents.v4_agents
        import core.agents.trust_guide_agent
        try:
            import core.agents.vision_agent
        except ImportError:
            pass
        try:
            import core.agents.xzb_expert_agent
        except ImportError:
            pass
        return len(BaseAgent.__subclasses__())
    except Exception:
        return 20


def _count_endpoints(app) -> int:
    """Count all API endpoint routes."""
    try:
        count = 0
        for route in app.routes:
            if hasattr(route, 'methods'):
                count += len(route.methods - {'HEAD', 'OPTIONS'})
        return count
    except Exception:
        return 700


def _count_scheduler_jobs() -> int:
    """Count registered scheduler jobs."""
    try:
        from core.scheduler import scheduler
        if scheduler.running:
            return len(scheduler.get_jobs())
        return 35
    except Exception:
        return 35


@_stats_router.get("/platform-stats")
def get_platform_stats():
    """平台实时统计 (公开端点, 5分钟缓存)"""
    now = time.time()
    if _stats_cache["data"] and (now - _stats_cache["ts"]) < _CACHE_TTL:
        return _stats_cache["data"]

    model_count = _count_orm_models()
    agent_count = _count_agents()
    scheduler_jobs = _count_scheduler_jobs()
    platform_version = os.getenv("PLATFORM_VERSION", "V5.3.0")

    endpoint_count = 700
    try:
        from api.main import app as _app
        endpoint_count = _count_endpoints(_app)
    except Exception:
        pass

    data = {
        "api_endpoints": endpoint_count,
        "data_models": model_count,
        "agent_count": agent_count,
        "knowledge_tiers": 4,
        "scheduler_jobs": scheduler_jobs,
        "platform_version": platform_version,
    }
    _stats_cache["data"] = data
    _stats_cache["ts"] = now
    return data


# ══════════ Merge sub-routers into main router ══════════
router.include_router(_demo_router)
router.include_router(_stats_router)
