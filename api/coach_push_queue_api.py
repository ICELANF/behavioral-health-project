# -*- coding: utf-8 -*-
"""
教练推送审批队列 API
Coach Push Queue API

前缀: /api/v1/coach/push-queue
权限: require_coach_or_admin
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User
from api.dependencies import get_current_user, require_coach_or_admin, require_admin
from core import coach_push_queue_service as queue_svc

router = APIRouter(prefix="/api/v1/coach/push-queue", tags=["coach-push-queue"])


# ============================================
# Pydantic 模型
# ============================================

class ApproveBody(BaseModel):
    content_override: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    coach_note: Optional[str] = None


class RejectBody(BaseModel):
    coach_note: Optional[str] = None


class BatchApproveBody(BaseModel):
    item_ids: List[int] = Field(..., min_length=1)


class UpdateItemBody(BaseModel):
    content: Optional[str] = None
    scheduled_time: Optional[datetime] = None


# ============================================
# 端点
# ============================================

@router.get("")
def list_queue_items(
    student_id: Optional[int] = Query(None),
    source_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: str = Query("pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取待审批推送列表"""
    return queue_svc.get_pending_items(
        db,
        coach_id=current_user.id,
        student_id=student_id,
        source_type=source_type,
        priority=priority,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
def queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """各状态数量统计"""
    return queue_svc.get_stats(db, coach_id=current_user.id)


@router.put("/{item_id}")
def update_queue_item(
    item_id: int,
    body: UpdateItemBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """修改待审批条目的内容/时间"""
    try:
        item = queue_svc.update_item(
            db,
            item_id=item_id,
            coach_id=current_user.id,
            content=body.content,
            scheduled_time=body.scheduled_time,
        )
        return {"message": "已更新", "item": queue_svc._item_to_dict(item)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{item_id}/approve")
def approve_queue_item(
    item_id: int,
    body: ApproveBody = ApproveBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审批通过"""
    try:
        item = queue_svc.approve_item(
            db,
            item_id=item_id,
            coach_id=current_user.id,
            content_override=body.content_override,
            scheduled_time=body.scheduled_time,
            coach_note=body.coach_note,
        )
        return {"message": "已审批通过", "item": queue_svc._item_to_dict(item)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{item_id}/reject")
def reject_queue_item(
    item_id: int,
    body: RejectBody = RejectBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """拒绝推送"""
    try:
        item = queue_svc.reject_item(
            db,
            item_id=item_id,
            coach_id=current_user.id,
            coach_note=body.coach_note,
        )
        return {"message": "已拒绝", "item": queue_svc._item_to_dict(item)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-approve")
def batch_approve_items(
    body: BatchApproveBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批量审批通过"""
    count = queue_svc.batch_approve(
        db,
        item_ids=body.item_ids,
        coach_id=current_user.id,
    )
    return {"message": f"已批量审批 {count} 条", "approved_count": count}


# ============================================
# 审批历史 + 详情
# ============================================

@router.get("/history")
def list_history(
    status: Optional[str] = Query(None, description="过滤状态: approved/rejected/sent/expired"),
    student_id: Optional[int] = Query(None),
    source_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练审批历史列表"""
    df = datetime.fromisoformat(date_from) if date_from else None
    dt = datetime.fromisoformat(date_to) if date_to else None
    return queue_svc.get_history(
        db,
        coach_id=current_user.id,
        status=status,
        student_id=student_id,
        source_type=source_type,
        date_from=df,
        date_to=dt,
        page=page,
        page_size=page_size,
    )


@router.get("/{item_id}/detail")
def get_queue_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取推送条目详情"""
    try:
        return queue_svc.get_item_detail(db, item_id=item_id, coach_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# 审批效率分析
# ============================================

@router.get("/analytics")
def get_coach_analytics(
    period: int = Query(7, ge=1, le=90, description="统计周期(天)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练个人审批效率分析"""
    return queue_svc.get_review_analytics(db, coach_id=current_user.id, period_days=period)


@router.get("/analytics/admin")
def get_admin_analytics(
    period: int = Query(7, ge=1, le=90, description="统计周期(天)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员全局审批效率分析（含各教练排行）"""
    return queue_svc.get_review_analytics(db, coach_id=None, period_days=period)


# ============================================
# /api/v1/coach-push/* — 前端兼容别名路由
# CoachHome.vue 使用 /api/v1/coach-push/pending 和 /{id}/approve|reject
# ============================================

alias_router = APIRouter(prefix="/api/v1/coach-push", tags=["coach-push-alias"])


@alias_router.get("/pending")
def get_pending_pushes(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """待审批推送列表 (CoachHome.vue 兼容别名 — 实际由 push-queue 提供)"""
    return queue_svc.get_pending_items(
        db,
        coach_id=current_user.id,
        status="pending",
        page=1,
        page_size=limit,
    )


@alias_router.post("/{item_id}/approve")
def alias_approve(
    item_id: int,
    body: ApproveBody = ApproveBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审批通过 (兼容别名)"""
    try:
        item = queue_svc.approve_item(
            db,
            item_id=item_id,
            coach_id=current_user.id,
            content_override=body.content_override,
            scheduled_time=body.scheduled_time,
            coach_note=body.coach_note,
        )
        return {"message": "已审批通过", "item": queue_svc._item_to_dict(item)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@alias_router.post("/{item_id}/reject")
def alias_reject(
    item_id: int,
    body: RejectBody = RejectBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """拒绝推送 (兼容别名)"""
    try:
        item = queue_svc.reject_item(
            db,
            item_id=item_id,
            coach_id=current_user.id,
            coach_note=body.coach_note,
        )
        return {"message": "已拒绝", "item": queue_svc._item_to_dict(item)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
